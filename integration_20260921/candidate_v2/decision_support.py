"""Deterministic facts and narrow corrections from the supplied DACON material.

No learned model, sample IDs, gold-label lookup, network, or mutable test-wide
statistics. A correction is applied only AFTER a valid fixed-LLM judgment.
Ambiguous facts are left to the LLM. Monetary constants come from the supplied
snapshot, not current external law. See the separate development report.
"""
from __future__ import annotations

import re
import unicodedata
from bisect import bisect_left
from dataclasses import dataclass
from datetime import datetime, date
from qualification_support import ProcurementSupport, qualification_spans

# Explicit-clause rules here are combined with scoped procurement rules in
# qualification_support.py only after a normal valid fixed-model judgment.
OVERRIDE_ITEMS = frozenset({1,2,3,4,5,6,7,8,9,19,21,22,23,24})


def dense(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", str(text))).lower()


def money(text):
    """Arabic numerals with Korean monetary units; do not guess written words."""
    value = dense(text).replace(",", "").replace("원", "")
    if not re.fullmatch(r"[\d.조억만천백십]+", value):
        return None
    total = group = number = 0.0
    try:
        for token in re.findall(r"\d+(?:\.\d+)?|[조억만천백십]", value):
            if token[0].isdigit():
                number = float(token)
            elif token in "천백십":
                group += (number or 1) * {"천":1000, "백":100, "십":10}[token]
                number = 0
            else:
                total += (group + number or 1) * {"만":10000, "억":100000000, "조":1000000000000}[token]
                group = number = 0
        return int(round(total + group + number))
    except (ValueError, OverflowError):
        return None


AMOUNT = r"\d[\d,.조억만천백십]*원"
REGIONS = r"서울특별시|부산광역시|대구광역시|인천광역시|광주광역시|대전광역시|울산광역시|세종특별자치시|경기도|강원(?:특별자치)?도|충청북도|충청남도|전북(?:특별자치도)?|전라북도|전라남도|경상북도|경상남도|제주(?:특별자치)?도"


@dataclass
class Document:
    text: str
    kind: str

    def __post_init__(self):
        self.text = unicodedata.normalize("NFC", self.text)
        self.positions = [i for i, c in enumerate(self.text) if not c.isspace()]
        self.flat = "".join(self.text[i].lower() for i in self.positions)

    def window(self, start, end, before=180, after=120):
        a, b = max(0,start-before), min(len(self.flat),end+after)
        if not self.positions:
            return a,b,""
        raw_a,raw_b=self.positions[a],self.positions[b-1]+1
        raw_start,raw_end=self.positions[start],self.positions[end-1]+1
        separators=list(re.finditer(r"\n\s*\n|(?m:^)[ \t]*(?:[가-하][.)]|\d+[.)]|[①-⑳ㅇ○◦•※])",self.text[raw_a:raw_b]))
        for separator in separators:
            point=raw_a+separator.start()
            if point<raw_start:
                a=max(a,bisect_left(self.positions,point))
            elif point>=raw_end:
                b=min(b,bisect_left(self.positions,point))
                break
        return a,b,self.flat[a:b]

    def quote(self, start, end, padding=30):
        if not self.positions or start >= len(self.positions):
            return ""
        a = self.positions[max(0, start - padding)]
        b = self.positions[min(len(self.positions) - 1, end + padding - 1)] + 1
        # Start at the next line only when it does not remove the match.
        boundary = self.text.find("\n", a, self.positions[start])
        if boundary >= 0:
            a = boundary + 1
        return self.text[a:b][:480].strip()


class DecisionSupport:
    def __init__(self, catalog_rows):
        self.catalog = {r["세부품명번호"].strip(): r for r in catalog_rows}
        self.procurement = ProcurementSupport(catalog_rows)

    def analyze(self, rec):
        docs = [Document(d["text"], d["type"]) for d in rec["docs"]]
        notices = [d for d in docs if d.kind == "공고문"]
        meta = rec["meta"]
        whole = "\n".join(d.flat for d in docs)
        notice = "\n".join(d.flat for d in notices)
        law = str(meta.get("적용계약법") or "")
        local = "지방" in law
        national = "국가" in law
        construction = "공사" in str(meta.get("업무구분") or "")
        negotiated = "협상" in str(meta.get("낙찰방법") or "") or "협상에의한계약" in notice
        small_contract = ("수의" in str(meta.get("계약방법") or "") or "소액수의" in str(meta.get("낙찰방법") or "")
                          or bool(re.search(r"소액수의|수의견적|2인이상견적", notice[:7000])))
        price = meta.get("입찰추정가격")
        budget = meta.get("배정예산금액")
        price = int(price) if isinstance(price, (int, float)) and price > 0 else None
        budget = int(budget) if isinstance(budget, (int, float)) and budget > 0 else None
        corrections = {}
        metadata_differences = []

        def add(item, document, start, end, reason):
            quote = document.quote(start, end)
            if quote and not quote.startswith(("=", "+", "@")):
                corrections.setdefault(item, {"value":1, "evidence":quote, "reason":reason})

        # Explicitly named estimate only. A table with several monetary labels
        # before its first amount is ambiguous and intentionally not parsed.
        estimates = []
        for doc in notices:
            for match in re.finditer(r"추정가격(?:[:：금￦₩]|\([^)]{0,20}\))*?(" + AMOUNT + r")", doc.flat):
                val = money(match.group(1))
                tail=doc.flat[match.end():match.end()+40]
                surrounding=doc.flat[max(0,match.start()-40):match.end()+70]
                if (val and val > 1000 and not re.match(r"(?:미만|이하|이상|초과)",tail)
                        and not re.search(r"단가|톤당|단위당|부가(?:가치)?세(?:등일체의비용)?포함",surrounding)):
                    estimates.append((val, doc, match))
        if estimates and len({x[0] for x in estimates}) == 1:
            document_price, doc, match = estimates[0]
            if price and abs(document_price - price) > max(100, price * .02) and "단가입찰" not in notice:
                add(24, doc, match.start(), match.end(), "본문의 명시 추정가격과 같은 종류의 메타 금액이 유의하게 불일치")
            price = document_price

        facts = {"적용계약법_meta":law, "본문우선_추정가격":price, "사업예산_meta":budget,
                 "소액수의여부":small_contract, "협상계약여부":negotiated,
                 "설명":"제공 원문에서 추출한 적용조건이다. 불명확한 사실은 모델이 원문으로 확인한다."}

        # Monetary and geographic clauses: only enforce explicit requirements
        # in the notice, not scoring forms or hypothetical law examples.
        performance = []
        regions = []
        region_exception = bool(re.search(r"10(?:인|개사|개업체)미만|인접.{0,25}(?:납품지|청사|걸쳐)|지역제한.{0,30}예외", notice))
        for doc in notices:
            for match in re.finditer(r"본점|본사(?!업)|주된(?:영업소|사무소)|법인등기부상", doc.flat):
                a,b,part=doc.window(match.start(),match.end(),80,350)
                if re.search(REGIONS + r"|단위=기초|기초자치단체", part) and re.search(r"업체|자격|제한|참가|하여야|이어야|있는자|둔자|있어야", part):
                    regions.append((doc, a, b, part))
            for match in re.finditer(r"실적", doc.flat):
                a,b,part=doc.window(match.start(),match.end())
                # Close obligatory wording, with optional parentheses.
                mandatory = re.search(r"실적.{0,70}(?:있는(?:업체|자)|있어야|보유한|보유하여|갖춘|제출이가능한업체)|실적.{0,40}이상.{0,30}(?:업체|보유)|실적이.{0,25}이상", part)
                amounts = list(re.finditer(AMOUNT, part))
                if not mandatory or not amounts:
                    continue
                if re.search(r"배점|평가점수|정량평가|평가기준표|심사항목|가점|배제해서는", part):
                    continue
                values = [money(x.group()) for x in amounts]
                values = [v for v in values if v and v >= 10000]
                if not values:
                    continue
                amount = max(values)
                performance.append((doc,a,b,part,amount))
                if not construction and not small_contract and price and price < 230000000:
                    add(2,doc,a,b,"고시금액 미만 공고의 필수 금액 실적제한")
                if not construction and budget and amount > budget:
                    add(3,doc,a,b,"필수 실적금액이 사업예산을 초과")
                institution=re.search(r"(?:국가기관|공공기관|정부투자기관|대학병원|국공립|지방자치단체).{0,70}(?:발주|납품|시행|이행|운행|용역).{0,55}실적|(?:중고등학교|초등학교|중학교|고등학교)학생대상.{0,50}실적",part)
                if institution and not re.search(r"민간|공공기관이외|구분없이", part):
                    add(4,doc,a,b,"특정 발주기관 실적만 참가자격으로 요구")
            for match in re.finditer(r"(?:대학(?:교)?|산학협력단|연구기관|비영리법인)(?:\]|\)){0,2}만.{0,25}(?:참여|참가|입찰)|(?:대학(?:교)?|산학협력단|연구기관)에한(?:정|하여).{0,35}(?:참가|입찰|참여)", doc.flat):
                add(1,doc,match.start(),match.end(),"특정 기관 유형만 입찰참가 허용")
            for match in re.finditer(r"(?:최소(?:참여)?지분(?:율)?|최소출자비율).{0,18}?(\d+(?:\.\d+)?)%",doc.flat):
                # Split performance contracts do not have the joint minimum.
                if "분담이행" in notice and "공동이행" not in notice:
                    continue
                minimum = 5 if local else 10 if national else None
                if minimum and not construction and float(match.group(1)) < minimum:
                    add(21,doc,match.start(),match.end(),"공동이행 최소지분이 해당 계약법 기준보다 낮음")
            for match in re.finditer(r"(?:물품공급|기술지원|공급)[·ㆍ,‧/및\w()]{0,50}?확약서|제조회사공급증명원.{0,25}확약서", doc.flat):
                a,b,part=doc.window(match.start(),match.end(),120,220)
                pre = re.search(r"(?:입찰|전자입찰|제안서|견적서)(?:서|참가)?(?:제출|등록)?(?:마감일|마감|등록일)?(?:전일|전까지|전|시)(?:까지)?",part)
                waived = re.search(r'확약서.{0,55}(?:제출|발급|보유|소지)(?:할)?(?:필요가?없|하지않아도|하지아니하여도|을요구하지)',part)
                if pre and not waived and re.search(r"보유|제출하여야|제출해야|발급|소지|구비|제출할것",part):
                    add(19,doc,a,b,"입찰 전에 확약서 발급·보유·제출 요구")
                if '제조회사공급증명원' in part and re.search(r'입찰관련서류|제안서제출',doc.flat[max(0,a-400):a]):
                    add(19,doc,a,b,"제안서 제출서류에 제조사 공급증명원과 확약서 필수 제출")
            # Supplier location clauses may use a short province name and
            # omit the words 'head office'. Restrict this to qualifications.
            for qa,qb in qualification_spans(doc):
                for match in re.finditer(r'(?:경북|경남|충북|충남|전남|전북|서울|부산|대구|인천|대전|광주|울산|세종|강원|제주)(?:도|시)?에소재한.{0,35}업체',doc.flat[qa:qb]):
                    a,b=qa+match.start(),qa+match.end()
                    part=doc.flat[a:b]
                    if not re.search(r'실적|사업자등록',doc.flat[max(qa,a-100):b]):continue
                    regions.append((doc,a,b,part))
                for m in re.finditer(r'\[지역:[^\]]*단위=기초[^\]]*\]지역업체',doc.flat[qa:qb]):
                    a,b=qa+m.start(),qa+m.end()
                    regions.append((doc,a,b,doc.flat[a:b]))
                for m in re.finditer(r'등록한자중.{0,180}(?:대학교|대학).{0,70}국공립연구기관가능',doc.flat[qa:qb]):
                    clause=doc.flat[qa+m.start():qa+m.end()]
                    if not re.search(r'기업|개인|민간|포함',clause):
                        add(1,doc,qa+m.start(),qa+m.end(),"참가등록자 중 대학·공공 연구기관 유형만 자격으로 열거")
            # Compare a location field only when its ordinary meaning is
            # explicit. An unspecified/null metadata list alone is not proof.
            for d,a,b,part in list(regions):
                if d is not doc:continue
                if meta.get('지역제한여부')=='N':
                    metadata_differences.append({'항목':'지역제한여부','meta':'N','본문':doc.quote(a,b,padding=0)})
                elif meta.get('지역제한여부')=='Y' and meta.get('제한지역코드목록'):
                    aliases={'강원도':'강원특별자치도','전북':'전북특별자치도','전라북도':'전북특별자치도','제주도':'제주특별자치도'}
                    body={aliases.get(x,x) for x in re.findall(REGIONS,part)}
                    registered={aliases.get(x,x) for x in re.findall(REGIONS,str(meta['제한지역코드목록']))}
                    if body and registered and not body.issubset(registered):
                        metadata_differences.append({'항목':'제한지역코드목록','meta':str(meta['제한지역코드목록']),'본문':doc.quote(a,b,padding=0)})
            existing_codes=set(re.findall(r'\b\d{4}\b',str(meta.get('면허업종제한목록') or '')))
            if existing_codes and meta.get('업종제한여부')=='Y':
                for qa,qb in qualification_spans(doc):
                    for m in re.finditer(r'(?:업종코드|업종번호|면허코드)[:：\[(]*(\d{4})[)\]]*.{0,80}(?:등록|신고|면허)',doc.flat[qa:qb]):
                        if m.group(1) not in existing_codes:
                            add(24,doc,qa+m.start(),qa+m.end(),"본문이 필수로 허용한 업종번호와 입력된 업종번호가 서로 다름")
            # A title's explicit price band is a same-field assertion; do not
            # confuse an assessment table or statutory threshold with it.
            for m in re.finditer(r'(?:제한경쟁|일반경쟁)[·ㆍ,](\d+)억원미만',doc.flat[:3000]):
                meta_price=meta.get('입찰추정가격')
                if isinstance(meta_price,(int,float)) and meta_price>=int(m.group(1))*100000000:
                    add(24,doc,m.start(),m.end(),"공고 명칭의 계약 추정가격 구간과 나라장터 입력 추정가격이 불일치")
        # Specification and meeting clauses may be in attachments, not only
        # in the notice. Search every provided document independently.
        for doc in docs:
            if doc.kind in {"규격서","과업지시서","제안요청서"}:
                patterns=[r"(?:제조사[·ㆍ/]?)?모델명\s*[:：][^\n]{3,140}",
                          r"[Cc]hipset\s*[:：]\s*[A-Za-z]+\d+\s+[A-Za-z]+\s+[A-Za-z]+[^\n]{0,70}",
                          r"\b[A-Z][A-Za-z]{1,}(?:\s+[A-Za-z]{2,}){1,3}\s+\d+[A-Za-z0-9./-]*[^\n]{0,90}일\s*것",
                          r"장\s*비\s*명\s*[^\n]{1,60}\([A-Za-z]{2,}-\d+[A-Za-z0-9-]*\)"]
                for pattern in patterns:
                    for match in re.finditer(pattern,doc.text):
                        nearby=doc.text[max(0,match.start()-45):match.end()+100]
                        if re.search(r"기존|예시|예를|참고|동등|상관없이",nearby):
                            continue
                        if not re.search(r"[A-Za-z]{2,}",match.group()):
                            continue
                        a=bisect_left(doc.positions,match.start());b=bisect_left(doc.positions,match.end())
                        add(9,doc,a,b,"규격·과업 문서의 구체적 제조사 모델 명시")
                for heading in re.finditer(r'모델명',doc.text):
                    block=doc.text[heading.end():heading.end()+320]
                    candidate=re.search(r'\b[A-Z][a-z]{2,}[ \t]+[A-Za-z][A-Za-z0-9/-]*[ \t]+\d+[A-Za-z0-9/-]*',block)
                    if candidate and not re.search(r'동등|예시|기존|호환|참고',block):
                        a=bisect_left(doc.positions,heading.end()+candidate.start())
                        b=bisect_left(doc.positions,heading.end()+candidate.end())
                        add(9,doc,a,b,"규격서 모델명 열에 특정 상용 장비와 모델번호를 지정")
            if negotiated:
                for match in re.finditer(r"(?:현장|사업|과업|제안요청서?|제안)?설명회",doc.flat):
                    a,b=max(0,match.start()-30),min(len(doc.flat),match.end()+200)
                    part=doc.flat[a:b]
                    # Bidder presentations to evaluation panels occur after
                    # submission; they are not the procurer's pre-bid briefing.
                    evaluation = (bool(re.search(r'평가위원|제안내용발표|발표평가|기술평가회의',part))
                                  and not re.search(r'입찰참가자격|입찰등록|제안서접수|입찰참가를',part))
                    optional = bool(re.search(r'(?:참석여부와?(?:는)?(?:상관|관계)없이|참석여부에관계없이|미참석.{0,25}(?:참가가능|참여가능)|불참.{0,25}불이익.{0,8}없)',part))
                    banned = re.search(r"(?:미참석|불참|참석하지(?:아니)?한).{0,50}(?:허용되지|제외|접수하지|불가|없음|않음)|참석(?:한자|업체).{0,35}(?:한하여|한해|부여|참가자격)",part)
                    if banned and not evaluation and not optional:
                        add(22,doc,a,b,"협상계약 설명회 참석을 입찰자격으로 제한")
                    required_attendee = re.search(r"설명회에참석한자(?:\(|[○ㅇ]|$)",part)
                    if required_attendee and not evaluation and not optional and "참가자격" in doc.flat[max(0,a-1800):a] and not re.search(r"상관없이|무관|선택|희망",part):
                        add(22,doc,a,b,"참가자격 조항에서 설명회 참석자를 필수조건으로 명시")
            if local and negotiated and price:
                try:
                    opening=datetime.strptime(str(meta.get("개찰예정일자")),"%Y%m%d").date()
                    published=datetime.strptime(str(meta.get("공고게시일자")),"%Y%m%d").date()
                except ValueError:
                    continue
                for match in re.finditer(r"(?:현장|사업|과업|제안요청서?)설명(?:회)?",doc.flat):
                    tail=doc.flat[match.end():match.end()+160]
                    when=re.search(r"(20\d{2})[.년/-](\d{1,2})[.월/-](\d{1,2})(?:[.일(]|$)",tail)
                    if not when or re.search(r"제출|접수|평가|갈음|생략|미실시|실시하지|개최하지",tail[:when.start()]):
                        continue
                    try:meeting=date(*(int(x) for x in when.groups()))
                    except ValueError:continue
                    minimum=40 if price>=1000000000 else 20 if price>=100000000 else 10
                    closes=[]
                    for original in notices:
                        for label in re.finditer(r'제안서(?:및가격입찰서)?(?:제출|접수)(?!완료후)',original.flat):
                            fragment=original.flat[label.end():label.end()+140]
                            dm=re.search(r'(20\d{2})[.년/-](\d{1,2})[.월/-](\d{1,2})(?:[.일(]|$)',fragment)
                            if dm and not re.search(r'평가|공고기간|설명회',fragment[:dm.start()]):
                                try:closes.append(date(*(int(x) for x in dm.groups())))
                                except ValueError:pass
                    closing=max(closes) if closes else opening
                    if (0<=(closing-meeting).days<minimum+1 or 0<=(meeting-published).days<8):
                        add(23,doc,match.start(),match.end()+when.end(),"지방 협상 설명회 일정이 7일 공고 또는 10·20·40일 준비기간 미달")

        if not construction and regions:
            doc,a,b,part=regions[0]
            # 500M is used only for local ordinary non-technical goods/services;
            # uncertain local technical thresholds remain a model decision.
            technical = bool(re.search(r"건설기술|건축사|엔지니어링|정밀안전진단|안전점검",str(meta.get("면허업종제한목록") or "")))
            limit = 500000000 if local and not technical else 230000000 if national else None
            if limit and price and price >= limit and not small_contract:
                add(5,doc,a,b,"지역제한 허용금액 이상의 일반 물품·용역")
            if limit and price and price < limit and not small_contract:
                for d,x,y,p in regions:
                    # Anonymization markers in the supplied notices encode
                    # municipal granularity without needing a city-name list.
                    basic=("단위=기초" in p or "기초자치단체" in p or
                           (meta.get('지역제한여부')=='Y' and '단위=기초' in str(meta.get('제한지역코드목록') or '') and re.search(r'소재지|본점|영업소',p)))
                    if basic:
                        add(6,d,x,y,"일반 경쟁입찰의 시군구 단위 지역제한")
                    aliases={"강원도":"강원특별자치도","전북":"전북특별자치도","전라북도":"전북특별자치도","제주도":"제주특별자치도"}
                    names={aliases.get(x,x) for x in re.findall(REGIONS,p)}
                    if len(names)>1 and not region_exception:
                        add(7,d,x,y,"복수 시도 지역제한과 예외사유 불명확")
            if performance and not small_contract:
                d,x,y,_,_=performance[0]
                add(8,d,x,y,"참가 필수 실적과 본점 소재지 지역제한 중복")
            if not small_contract:
                for d,x,y,p in regions:
                    if re.search(r'실적이(?:우수한|있는)업체|실적보유업체',p):
                        add(8,d,x,y,"지역과 실적 보유를 같은 참가자격 조항에서 동시에 요구")

        corrections={i:x for i,x in corrections.items() if i in OVERRIDE_ITEMS}
        procurement_facts, procurement_changes = self.procurement.analyze(rec, docs, price, budget, small_contract)
        facts.update(procurement_facts)
        # v17 concerns an overly broad size restriction below 100M.  A
        # binding small-enterprise clause is the opposite signal: it does not
        # admit middle enterprises, even when a generic SME certificate is
        # mentioned elsewhere.  Keep the override narrow and evidence-backed;
        # ambiguous/no-size cases remain fixed-model decisions.
        if (price is not None and price < 100_000_000
                and facts.get("필수소기업조항")
                and 17 not in corrections):
            corrections[17] = {
                "value": 0, "evidence": "",
                "reason": "1억원 미만에서 소기업·소상공인으로 제한하는 참가자격 조항 확인",
            }
        distinct_differences=[]
        for candidate in metadata_differences:
            if candidate not in distinct_differences:
                distinct_differences.append(candidate)
        facts['메타본문_대조후보']=distinct_differences[:3]
        corrections.update(procurement_changes)
        # v13 is defined only for 중기간 경쟁제품.  The model can mistake a
        # generic 소기업·소상공인 eligibility clause in services/ordinary
        # goods (or an unresolved item classification) for this specific
        # competition-product restriction.  Suppress that out-of-scope
        # positive while preserving evidence-backed competition-product
        # corrections.
        if facts.get('품목상태') != '경쟁제품':
            corrections[13] = {
                'value': 0, 'evidence': '',
                'reason': 'v13은 중기간 경쟁제품에만 적용되는 항목',
            }
        # A product/specification list often names compatible equipment or a
        # reference model.  v9 concerns a model imposed as a participation or
        # performance requirement, not a catalogue/spec table entry.  When
        # model-like tokens appear without an explicit requirement marker,
        # suppress a model-only positive.
        model_seen = False
        restrictive_model = False
        model_like = False
        for doc in docs:
            if doc.kind not in {'규격서', '과업지시서', '제안요청서'}:
                continue
            for term in ('모델명', '제조사', '호환', '전용', '장비명'):
                start = 0
                while True:
                    at = doc.text.find(term, start)
                    if at < 0:
                        break
                    model_seen = True
                    window = doc.text[max(0, at - 100):at + 260]
                    if term in {'모델명', '제조사'} and re.search(r'(?:지정|사용할\s*것|사용해야|이어야|필수|만\s*가능|동일\s*모델)', window):
                        restrictive_model = True
                    start = at + len(term)
            if re.search(r'\b[A-Z][A-Za-z]{2,}[- ]?\d+[A-Za-z0-9-]*\b', doc.text):
                model_like = True
        benign_model_context = model_like or any('기술보유' in d.text for d in docs)
        if (model_seen or benign_model_context) and not restrictive_model and 9 not in corrections:
            corrections[9] = {
                'value': 0, 'evidence': '',
                'reason': '규격·호환 목록의 모델 언급으로 참가자격 특정 모델 강제가 아님',
            }
        # v21 concerns a required consortium share threshold. A bare
        # no-consortium/single-bid clause is not a share restriction.
        all_text = ' '.join(d.text for d in docs)
        if not re.search(r'지분\s*율|최소\s*지분|참여\s*비율', all_text):
            corrections[21] = {
                'value': 0, 'evidence': '',
                'reason': '공동수급 지분율·최소참여비율의 명시적 근거가 없음',
            }
        # Surface unusual qualifications for the LLM without blindly treating
        # every personnel/facility requirement as a legal violation.
        unusual=[]
        for doc in notices:
            for a,b in qualification_spans(doc):
                for m in re.finditer(r'전국.{0,30}(?:센터|지점)|\d+명이상.{0,18}(?:인력|직원)|교육\(?연수\)?시설.{0,25}보유|대학교.{0,50}국공립연구기관',doc.flat[a:b]):
                    unusual.append(doc.quote(a+m.start(),a+m.end())[:250])
        facts['특수기관_인력시설_요건']=unusual[:3]
        if not local or not negotiated:
            corrections[23]={'value':0,'evidence':'','reason':'v23은 지방계약법의 협상 계약에만 적용'}
        if not negotiated:
            corrections[22]={'value':0,'evidence':'','reason':'v22는 협상 계약에만 적용'}
        # v24 is a metadata/document consistency check. Keep model positives
        # only when an explicit quoted mismatch was detected above; incidental
        # mentions of estimates or evaluation formulas are not mismatches.
        if 24 not in corrections:
            corrections[24] = {
                'value': 0, 'evidence': '',
                'reason': '명시적인 본문-메타데이터 불일치 근거가 없어 v24 양성 보정',
            }
        facts['적용대상이_아닌항목']=[f'v{i}' for i,x in sorted(corrections.items()) if not x['value']]
        facts["명시조건_보정후보"]={f"v{i}":{"판정":1,"조건":x["reason"],"원문":x["evidence"][:180]} for i,x in corrections.items() if x['value']}
        return facts, corrections

    def apply(self, rec, row):
        _, corrections = self.analyze(rec)
        for item, change in corrections.items():
            row[f"v{item}"]=change['value']
            row[f"e{item}"]="" if not change['value'] or item in {10,11,16,18,20} else change["evidence"]
        return row
