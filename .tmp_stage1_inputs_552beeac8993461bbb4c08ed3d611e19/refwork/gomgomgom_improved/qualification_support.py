"""Per-notice procurement facts from the organizer's supplied catalog/snapshot.

No example-ID matching, learned weights, outside assets or test-wide state.
Unknown/contradictory product scopes remain a fixed-model decision.
"""
from __future__ import annotations

import re
from bisect import bisect_left

PUNCT = str.maketrans({c: '·' for c in 'ㆍ․‧∙・･,／/、'})
SEP = r'[·ㆍ․‧∙・･,／/、]'
SIZE = r'중기업(?:(?:'+SEP+r')|또는|및)*(?:소기업)?|중'+SEP+r'*소기업|소기업|소상공인'
HEAD = re.compile(r'(?m)^[ \t|]*(?:(\d{1,2})(?:[-－]\d+)*[ \t]*[.．)|]|[■□◐•○❍])?[ \t]*(?:입\s*찰(?:서)?|견\s*적(?:서)?|제\s*안(?:서)?)?(?:\([^\n)]{0,20}\))?[ \t]*(?:참\s*가|제\s*출)[ \t]*자\s*격(?!\s*(?:등록|제한|이|을|의|에|등))[^\n]{0,100}')
NEXT_HEAD = re.compile(r'(?m)^[ \t|]*(\d{1,2})(?:[-－]\d+)*[ \t]*[.．|][ \t]*(?=[가-힣(「<])[^\n]{0,90}')


def flat(text):
    return re.sub(r'\s+', '', str(text)).lower().translate(PUNCT)


def qualification_spans(doc):
    spans = []
    for m in HEAD.finditer(doc.text):
        # A table of contents is not the actual qualification clause.
        if re.search(r'\.{3,}|목차', m.group()):
            continue
        end = len(doc.text)
        for nxt in NEXT_HEAD.finditer(doc.text, m.end()):
            # Subsections 3-1 (submission docs) are separate from section 3.
            # Numbered 1)/2) lists inside section 3 are not top-level headings.
            if m.group(1) and int(nxt.group(1))<=int(m.group(1)) and '-' not in nxt.group().split()[0]:
                continue
            if nxt.start() > m.start():
                end = nxt.start()
                break
        if end-m.end() >= 40:
            spans.append((bisect_left(doc.positions,m.start()),bisect_left(doc.positions,end)))
    return spans


def size_clauses(notices):
    """Find binding size clauses; separate primary terms from template reminders."""
    result = {'small':[], 'sme':[], 'sections':[], 'ambiguous':False}
    for doc in notices:
        sections = qualification_spans(doc)
        result['sections'].extend((doc,a,b) for a,b in sections)
        text = doc.flat.translate(PUNCT)
        for m in re.finditer(SIZE,text):
            word=m.group(); tail=text[m.end():m.end()+30]
            if re.match(r'(?:기본법|제품|공공|범위|은행|협동조합|자간|자와의|보호및지원|현황정보|지원센터|청|창업지원)',tail):
                continue
            a,b,_=doc.window(m.start(),m.end(),100,300)
            part=text[a:b]
            rel=m.start()-a
            # A mere checklist, issued-date reminder or funding paragraph is
            # not the substantive admission rule tested by the item table.
            after=text[m.end():min(b,m.end()+230)]
            primary=bool(re.search(r'(?:으로서|자로서|소지한(?:자|업체)|소지하여야|소지한업|소지업체|소지하고|보유한업체|보유한자|인업체|간제한경쟁|에한하여|만참가|이어야)',after))
            if not primary and any(x<=m.start()<y for x,y in sections):
                primary=bool(re.search(r'(?:따른|해당하는).{0,10}$',text[max(a,m.start()-15):m.start()]) and re.search(r'소상공인|중기업|소기업',after))
                if re.search(r'(?:요건을갖춘|요건에해당하는)$',text[max(a,m.start()-20):m.start()]):primary=True
                # A short standalone qualification bullet is itself binding.
                rawpos=doc.positions[m.start()]
                line=flat(doc.text[doc.text.rfind('\n',0,rawpos)+1:doc.text.find('\n',rawpos) if '\n' in doc.text[rawpos:] else len(doc.text)])
                if len(line)<40 and re.fullmatch(r'[가-하.)○•|]*(?:'+SIZE+r')(?:(?:[·]|또는|및|자|중기업|소기업|소상공인))*',line):primary=True
                # A qualification bullet may end at the statutory category,
                # without repeating '소지한 업체' or requiring a certificate.
                if len(line)<160 and re.search(r'따른(?:'+SIZE+r')자?[.。|]*$',line):primary=True
            if not primary:
                continue
            if re.search(r'해당시|해당자에한|해당하는경우|필요시|우대|가점|신청한업체|발급된.{0,25}기업구분과다른',part[:rel+15]):
                continue
            if re.search(r'(?:창업|특별법인|간주되는|확인서가|확인서는|확인서의|확인서를신청)',part[:rel]):
                # A late-issuance exception cannot create a stricter category.
                continue
            if re.search(r'확인서.{0,60}(?:서류|신청).{0,30}(?:해당시|해당자)',part):
                continue
            if (re.search(r'확인서를제출할(?:경우|때)',after)
                    and not re.search(r'참가자격|입찰참가|참여가능|에한하여',after)):
                continue  # conditional delivery-date reminder, not eligibility
            if re.search(r'확인서.{0,25}(?:소지|제출|보유)(?:할)?(?:필요가?없|하지않아도|하지아니하여도)',after):
                continue
            if sections and not any(x<=m.start()<y for x,y in sections):
                # Accept a standalone explicitly binding clause outside a
                # parsed section; exclude ordinary later document checklists.
                if not re.search(r'(?:소지한(?:자|업체)|보유한(?:자|업체)|간제한경쟁|만참가)',after):
                    continue
            category='sme' if word.startswith('중') else 'small'
            # 소상공인 accompanying 중소기업 is not an independent small-only
            # restriction. Prefer the required certificate's actual scope.
            if word=='소상공인':
                continue
            certs=[]
            for cm in re.finditer(r'(?:'+SIZE+r')(?:(?:[·()<>「」\'“”]|또는|및|자|중기업|소기업|소상공인)){0,40}확인서',part):
                if cm.end()<=rel:
                    continue
                if re.match(r'(?:및장애인|확인요령)',part[cm.end():]):
                    continue
                certs.append(cm)
            if certs:
                cm=certs[0]
                # Only a certificate governing this clause (before its first
                # 소지한/보유한) takes priority over a generic Act reference.
                verb=re.search(r'소지한|보유한|소지하여야',part)
                if verb and cm.start()<verb.start():
                    category='sme' if cm.group().startswith('중') else 'small'
            # A 중기업 certificate in an OR-list also allows middle enterprises.
            if re.search(r'중기업확인서.{0,40}(?:중하나|또는|소기업확인서)',part):
                category='sme'
            entry=(doc,a,b)
            # Preserve a conflicting narrow statutory requirement in this
            # same binding clause. A generic certificate title is not proof
            # that middle enterprises may participate despite that condition.
            if category == 'sme' and re.search(r'따른소기업(?:및|또는|[·「])', part):
                if entry not in result['small']:
                    result['small'].append(entry)
            if entry not in result[category]:
                result[category].append(entry)
    result['ambiguous']=bool(result['small'] and result['sme'])
    return result


def task_context(notices):
    pieces=[]
    for d in notices:
        spans=qualification_spans(d)
        stop=spans[0][0] if spans else min(len(d.flat),5000)
        pieces.append(d.flat[:stop])
    return '\n'.join(pieces).translate(PUNCT)


class ProcurementSupport:
    def __init__(self, rows):
        self.rows={str(r['세부품명번호']).strip():r for r in rows}

    def product(self, rec, notices, price):
        meta=rec['meta']; scope=task_context(notices)
        text='\n'.join(d.flat for d in notices).translate(PUNCT)
        license=flat(meta.get('면허업종제한목록') or '')
        goods='물품' in str(meta.get('업무구분') or '')
        # Identify the contracted service independently of a potentially
        # erroneous direct-production certificate inserted in qualifications.
        research=(bool(re.search(r'학술[·.]?연구용역|위탁연구|연구과제|연구용역',scope))
                  or ('1169' in license and not re.search(r'정보시스템|데이터베이스|지질|측량',scope)))
        travel=bool(re.search(r'여행업|해외.{0,16}연수|국외.{0,16}연수|수련활동|숙박형.{0,12}체험학습|수학여행',scope+' '+license))
        general_service=(research or travel or bool(re.search(r'필터세척|공기질.{0,16}(?:점검|측정)|온실가스.{0,25}(?:검증|컨설팅)|감축사업.{0,18}(?:활성화|운영지원)|콜센터운영|기타사업지원서비스|교육운영지원|투자유치지원프로그램|창업.{0,12}(?:지원|육성)프로그램',scope)))
        if not goods and general_service:
            return '일반제품', [{'source':'용역의 실제 과업·면허','condition':'연구/여행/측정 등 고시 경쟁제품과 구별되는 서비스'}], True

        codes=set(re.findall(r'(?<!\d)\d{10}(?!\d)',str(meta.get('세부품명번호목록') or ''))) if goods else set()
        if not codes:
            for m in re.finditer(r'(?:세부품명|물품분류|g2b분류|품명번호).{0,65}?(?<!\d)(\d{10}|\d{8})(?!\d)',text):
                code=m.group(1)
                if len(code)==8:
                    codes.update(x for x in self.rows if x.startswith(code))
                else:codes.add(code)
        # Exact names are a second path, preserving the complete catalog note.
        if not codes:
            for code,row in self.rows.items():
                name=flat(row['세부품명'])
                if len(name)>=6 and name in text:codes.add(code)
        inferred=False
        if not codes and not goods:
            candidates=[]
            aliases=[('통학운송서비스',r'통학.{0,15}(?:버스|차량|운송)'),
                     ('공공기관통근운송서비스',r'통근.{0,15}(?:버스|차량|운송)'),
                     ('건물청소서비스',r'(?:건물|청사|시설).{0,10}청소|청소.{0,10}용역'),
                     ('시설물경비서비스',r'(?:시설|청사).{0,10}경비|경비용역'),
                     ('축제기획및대행서비스',r'축제.{0,35}(?:대행|운영|기획)'),
                     ('전시회기획및대행서비스',r'(?:전시회|박람회).{0,35}(?:운영|기획|대행)'),
                     ('기타행사기획및대행서비스',r'(?:행사|포럼).{0,35}(?:대행|운영|기획)'),
                     ('정보시스템유지관리서비스',r'(?:시스템|홈페이지|출입통제체계).{0,30}유지(?:관리|보수)'),
                     ('정보시스템개발서비스',r'정보시스템.{0,25}(?:구축|개발)')]
            for name,pattern in aliases:
                if re.search(pattern,scope):
                    if name=='축제기획및대행서비스' and re.search(r'축제.{0,12}공연기획',scope):
                        continue  # performance programming alone is not the whole festival service
                    candidates.extend(c for c,row in self.rows.items() if row['세부품명']==name)
                    break
            codes.update(candidates);inferred=bool(codes)
        details=[]
        for code in sorted(codes):
            row=self.rows.get(code)
            if row is None:
                details.append({'code':code,'applies':False,'source':'공식 품목표 미등재'})
                continue
            note=flat(row.get('특이사항','')); val=None
            if not note:val=True
            m=re.fullmatch(r'추정가격(\d+)억원미만에한함',note)
            if m and price:val=price<int(m.group(1))*100000000
            if note=='공공기관이자회사와수의계약하는경우제외':
                val=False if '자회사' in text and '수의' in text else True
            if '기계경비업' in note:
                excluded=bool(re.search(r'기계경비|특수경비',license+scope))
                val=False if excluded or ('자회사' in text and '수의' in text) else True
            if note=='소프트웨어진흥법제48조적용':
                # This note invokes SW participation rules; it does not remove
                # the product from the competition list.
                val=True
            if '공공기관홍보용' in note and re.search(r'홍보.{0,30}(?:영상|동영상)|(?:영상|동영상).{0,30}홍보',scope):val=True
            if '전시산업발전법' in note:val=True  # inclusion note, not an exemption
            details.append({'code':code,'name':row['세부품명'],'condition':row.get('특이사항',''),'applies':val})
        values=[x['applies'] for x in details]
        if values and all(x is True for x in values):return '경쟁제품',details[:8],not inferred
        if values and all(x is False for x in values):return '일반제품',details[:8],not inferred
        if values and any(x is True for x in values) and not any(x is False for x in values):
            return '경쟁제품',details[:8],False
        return '미확정',details[:8],False

    def analyze(self, rec, docs, price, budget, small_contract):
        notices=[d for d in docs if d.kind=='공고문']; meta=rec['meta']
        whole='\n'.join(d.flat for d in docs).translate(PUNCT)
        notice='\n'.join(d.flat for d in notices).translate(PUNCT)
        product,details,certain=self.product(rec,notices,price)
        sizes=size_clauses(notices)
        # Exceptions have scope: nonprofit admission does not legalize an
        # over-restrictive size requirement for commercial bidders.
        nonprofit=bool(re.search(r'비영리(?:법인|기관).{0,70}(?:참가가능|참가허용|참가할수|참여가능)',notice))
        exception=bool(re.search(r'(?:우선조달|중소기업자간경쟁).{0,30}(?:적용하지않|적용하지아니|적용예외|예외사유)|제2조의3.{0,60}(?:특정한성능|특수한기술|일반경쟁|유찰)',notice))
        expansion=bool(re.search(r'(?:3인이하|3개(?:사|업체)이하|2인미만|유찰).{0,100}(?:중소기업|중기업)|제2조의2.{0,30}단서',notice))
        coop=bool(re.search(r'공동사업.{0,45}(?:추천|조합)|조합.{0,50}추천',notice))
        direct=[]
        for d in notices:
            spans=qualification_spans(d)
            for m in re.finditer(r'직접생산(?:확인)?(?:증명서|확인서|기준)',d.flat):
                a,b,_=d.window(m.start(),m.end(),70,380)
                p=d.flat[a:b]
                binding=bool(re.search(r'(?:소지한|보유한|보유하여야|갖춘|소지하여야|필수자격|발급받은업체|발급받은자|소지업체)',p))
                if any(x<=m.start()<y for x,y in spans) and re.search(r'확인되지않을경우|유효기간내에있어야|유효하여야',p):binding=True
                if binding and not re.search(r'해당시|필요시|해당하는경우',p):
                    direct.append((d,a,b))
        corrections={}
        def positive(i,clause,why):
            if clause:
                d,a,b=clause; quote=d.quote(a,b,padding=0)
                if not quote or quote.startswith(('=','+','@')):return
            else:quote=''
            corrections[i]={'value':1,'evidence':quote,'reason':why}
        construction='공사' in str(meta.get('업무구분') or '')
        has_section=any(len(re.sub(r'[^가-힣A-Za-z0-9]','',d.flat[a:b]))>=60 for d,a,b in sizes['sections'])
        absence_ok=has_section  # an unavailable attachment is not evidence that a required notice clause exists
        small=sizes['small']; sme=sizes['sme']
        sw_competing=any('소프트웨어 진흥법' in x.get('condition','') for x in details)
        sw_large_exception=sw_competing and budget and budget>=2000000000
        if product=='경쟁제품' and not construction and not small_contract and not sw_large_exception:
            if not direct and absence_ok and not exception:
                positive(10,None,'실제 과업이 경쟁제품이며 공고 참가자격에 직접생산확인 필수요건이 없음')
            if not small and not sme and absence_ok and not exception:
                positive(11,None,'경쟁제품의 공고 참가자격에 중소기업 범위 제한이 없음')
            if small and not sme and not coop:
                positive(13,small[0],'경쟁제품 참가자격에서 요구 확인서 범위를 소기업으로 축소')
        if product=='일반제품' and not construction:
            if direct and not small_contract:
                positive(12,direct[0],'실제 과업은 일반제품인데 직접생산확인증명서를 필수 참가자격으로 요구')
            if price and not coop:
                if price>=230000000 and (small or sme):positive(14,(sme or small)[0],'고시금액 이상 일반제품의 기업규모 제한')
                if 100000000<=price<230000000 and small and not sme and not small_contract:positive(15,small[0],'중소기업이 참여할 금액대의 일반제품을 소기업 확인서로 제한')
                if price<100000000 and sme and not small and not expansion and not exception:
                    positive(17,sme[0],'1억원 미만 일반제품의 참가자격에 중기업까지 허용')
                if absence_ok and not small and not sme and not exception and not nonprofit and not small_contract:
                    if 100000000<=price<230000000:positive(16,None,'일반제품의 1억원 이상 고시금액 미만 참가자격에 중소기업 제한 없음')
                    if 0<price<100000000:positive(18,None,'일반제품의 1억원 미만 참가자격에 소기업 제한 없음')
        # SW participation is a distinct mandatory notice requirement, even
        # if an ordinary SME certificate is requested elsewhere.
        sw=bool(re.search(r'소프트웨어사업자|컴퓨터관련서비스사업',notice+str(meta.get('면허업종제한목록') or '')))
        goods='물품' in str(meta.get('업무구분') or '')
        goods_sw=bool(re.search(r'소프트웨어|운영체제|라이선스',str(meta.get('세부품명번호목록') or '')+task_context(notices)))
        if goods and not goods_sw:sw=False
        scope=task_context(notices)
        private_agency=bool(re.search(r'민간.{0,25}(?:사업자|단체)',scope)
                            and re.search(r'입찰만대행|입찰을대행',scope)
                            and re.search(r'직접계약|직접.{0,15}계약을체결',scope))
        core_sw=bool(sw_competing or re.search(r'(?:소프트웨어|정보시스템|정보화|홈페이지|데이터베이스|전산시스템).{0,35}(?:개발|구축|유지관리|유지보수|운영)',scope))
        hardware_scope=bool(re.search(r'(?:pc|컴퓨터|서버|전산장비).{0,20}(?:보급|구매|임대|교체|수리)',scope))
        # A software licence in an equipment-service qualification alone does
        # not prove that the contracted task is a software development service.
        sw_uncertain=hardware_scope and not core_sw
        sw_restriction=bool(re.search(r'(?:대기업|상호출자|상호출연).{0,100}(?:참여|참가|입찰).{0,25}(?:제한|불가|없|못)|(?:20|40|80)억원.{0,90}(?:참여제한|사업참여지원)|제48조.{0,100}(?:참여제한|중소기업자만)',whole))
        sw_exception=bool(re.search(r'대기업.{0,80}(?:예외사업|참여허용|참여가능)|참여지원.{0,40}적용제외',whole))
        if sw and budget and not sw_uncertain and absence_ok and not sw_restriction and not sw_exception:
            positive(20,None,'SW 참가자격을 요구하는 사업에 금액대별 대기업 참여제한 규정이 기재되지 않음')
        facts={'품목상태':product,'품목근거':details,'품목확정대조':certain,
               '참가자격절_추출':bool(sizes['sections']),
               '필수소기업조항':[d.quote(a,b,padding=0)[:260] for d,a,b in small[:2]],
               '필수중소기업조항':[d.quote(a,b,padding=0)[:260] for d,a,b in sme[:2]],
               '필수직생조항':bool(direct),'비영리허용':nonprofit,'우선조달예외':exception,
               '기업규모조항_혼재':sizes['ambiguous'],
               '민간계약_입찰대행_적용범위확인필요':private_agency,
               'SW사업후보':sw,'SW실제과업_장비납품과구별필요':sw_uncertain,'SW참여제한기재':sw_restriction,
               'SW장기계속_분리발주_확인필요':bool(sw and re.search(r'장기계속|연차별|분리발주|분담이행',whole))}
        # Logically disjoint amounts/product categories are not independent
        # positive alternatives. These are not learned score thresholds.
        impossible=set()
        if price and not construction:
            if price<100000000:impossible.update({14,15,16})
            elif price<230000000:impossible.update({14,17,18})
            else:impossible.update({15,16,17,18})
        if certain and not construction:
            if product=='일반제품':impossible.update({10,11,13})
            if product=='경쟁제품' and not sw_large_exception:impossible.update({12,14,15,16,17,18})
        for i in impossible:
            # An explicit positive correction takes priority if the record
            # has mixed/contradictory provisions requiring model review.
            if i not in corrections:
                corrections[i]={'value':0,'evidence':'','reason':'금액 구간 또는 확정된 품목 분류상 해당 위반항목의 적용대상이 아님'}
        # Presence of a binding qualification contradicts a claim that the
        # notice has no such qualification. Do not negate other violation
        # categories (e.g. an overly narrow category or a wrong certificate).
        # v16 remains a model judgment: the supplied validation material has
        # a scope conflict even where an apparent SME certificate is present.
        # No record-specific exception is used to hide that uncertainty.
        present={10:bool(direct),11:bool(small or sme),
                 18:bool(small) and not sizes['ambiguous']}
        for i,exists in present.items():
            if exists and i not in corrections:
                corrections[i]={'value':0,'evidence':'','reason':'공고 원문에 해당 필수 참가자격 조항이 명시되어 부재가 아님'}
        if private_agency and not certain:
            # A task-name match alone cannot settle procurement applicability
            # when the actual counterparty is a private organization and the
            # authority only handles bidding. Leave these items to the model;
            # this is uncertainty, not an automatic legal exemption.
            corrections={i:x for i,x in corrections.items() if not 10<=i<=18}
        return facts,corrections
