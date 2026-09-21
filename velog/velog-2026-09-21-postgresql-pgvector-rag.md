# Python에서 PostgreSQL과 pgvector로 RAG 저장소 준비하기

RAG를 실습하면서 문서를 벡터 저장소에 저장하고 검색하는 흐름을 복습했다. 이번에는 PostgreSQL에 `pgvector` 확장을 연결해 문서와 임베딩을 관계형 테이블에 함께 저장할 준비를 해보았다.

## RAG에서 벡터 저장소가 필요한 이유

문서를 그대로 LLM에 전달하는 대신 다음 단계로 처리한다.

```text
문서 로딩 → 청킹 → 임베딩 → 벡터 저장 → 관련 문서 검색 → 답변 생성
```

질문과 의미가 가까운 문서 조각을 검색해 Prompt의 Context로 넣으면, 모델이 참고 자료를 기반으로 답변하도록 유도할 수 있다.

## PostgreSQL 연결

실습에서는 접속 정보와 비밀번호를 코드에 직접 공개하지 않고 환경 변수나 별도 보안 설정으로 관리해야 한다.

```python
import os
import psycopg

conn = psycopg.connect(os.environ["DATABASE_URL"])
print(conn.execute("SELECT version()").fetchone()[0])
```

먼저 데이터베이스 연결이 정상인지 확인한 뒤 확장을 활성화한다.

```python
conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
conn.commit()
```

## Python 어댑터 등록

`pgvector`의 Python 어댑터를 등록하면 Python 리스트 같은 값을 PostgreSQL의 `vector` 타입과 연결할 수 있다.

```python
from pgvector.psycopg import register_vector

register_vector(conn)
```

## vector 컬럼을 가진 테이블 만들기

임베딩 차원에 맞춰 vector 컬럼의 차원을 지정한다. 아래 예시는 1536차원 임베딩을 저장하는 문서 테이블이다.

```sql
CREATE TABLE IF NOT EXISTS documents (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536)
);
```

테이블을 만든 뒤에는 실제 스키마를 조회해 컬럼 타입이 예상대로 생성됐는지 확인한다.

```sql
SELECT a.attname, format_type(a.atttypid, a.atttypmod)
FROM pg_attribute a
WHERE a.attrelid = 'documents'::regclass
  AND a.attnum > 0
  AND NOT a.attisdropped;
```

## 이번 실습에서 배운 점

- 벡터 저장소도 데이터베이스의 테이블·스키마·트랜잭션 원칙 안에서 관리할 수 있다.
- `CREATE EXTENSION`과 Python 어댑터 등록은 서로 다른 단계다.
- 임베딩 모델의 차원과 `vector(n)`의 차원이 반드시 일치해야 한다.
- RAG 답변 품질은 DB 연결만으로 결정되지 않고 청킹, 검색 결과 수, Prompt의 근거 제한까지 함께 검증해야 한다.

## 다음 실습

다음 단계에서는 임베딩 데이터를 실제로 삽입하고, 거리 연산을 이용한 유사도 검색 SQL과 인덱스 적용 전후를 비교해볼 예정이다.

> 이 글은 로컬 실습 노트북을 바탕으로 정리한 게시 전 초안이다. 내부 IP, 비밀번호, 개인 경로는 포함하지 않았다.
