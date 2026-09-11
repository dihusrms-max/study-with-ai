# Python 기초 학습 정리: 파일 입출력, 함수, 예외 처리, 클래스

> 작성일: 2026-09-02

오늘은 파일에 내용을 작성하고 읽는 방법부터 함수의 반환값, 예외 처리, 클래스와 `self`까지 학습했다. 서로 다른 개념처럼 보이지만, 데이터를 저장하고 필요한 시점에 꺼내 사용하는 흐름으로 연결해 볼 수 있었다.

## 파일에 내용 작성하기

파일에 문자열을 작성할 때는 `write()`를 사용한다. 파일을 여는 모드에 따라 기존 내용을 유지할지 결정할 수 있다.

```python
with open("myeong-eon.txt", "w", encoding="utf-8") as file:
    file.write("시간은 금이다\n")
```

- `"w"`: 파일을 새로 작성한다. 기존 내용이 있다면 지운다.
- `"a"`: 기존 파일의 마지막에 내용을 추가한다.
- `"r"`: 파일을 읽는다.

여러 줄을 추가할 때는 리스트와 `for`문을 함께 사용할 수 있다.

```python
texts = [
    "시간은 금이다",
    "배움에는 끝이 없다",
    "오늘 할 일을 내일로 미루지 말자"
]

with open("myeong-eon.txt", "a", encoding="utf-8") as file:
    for text in texts:
        file.write(text + "\n")
```

여기서 `text`는 리스트에서 하나씩 꺼낸 문장이다. `"\n"`은 줄바꿈을 뜻하므로, 각 문장이 파일의 새 줄에 저장된다.

파일을 한 줄씩 읽을 때도 `for`문을 사용한다.

```python
with open("myeong-eon.txt", "r", encoding="utf-8") as file:
    for line in file:
        print(line.strip())
```

`write()`의 반환값은 작성한 문자열이 아니라 작성한 글자 수다. 따라서 보통은 반환값을 변수에 저장하지 않고 바로 사용한다.

## `append()`와 `write()`는 사용하는 대상이 다르다

`append()`는 리스트에 항목을 추가하는 메서드다.

```python
quotes = []
quotes.append("새 명언")
```

반면 파일에는 `append()`가 없으며, 파일 내용 추가는 `"a"` 모드와 `write()`를 사용한다.

```python
with open("myeong-eon.txt", "a", encoding="utf-8") as file:
    file.write("새 명언\n")
```

튜플도 리스트처럼 반복문으로 하나씩 꺼낼 수 있지만, 만들어진 뒤에는 값을 수정하거나 `append()`로 추가할 수 없다.

```python
texts = ("첫 번째", "두 번째", "세 번째")

for text in texts:
    print(text)
```

## 함수의 반환값과 여러 값 받기

여러 개의 숫자를 받아 합계를 구하는 함수는 `*nums`를 사용할 수 있다.

```python
def 합계(*nums):
    total = 0

    for i in nums:
        total += i

    return total
```

`total = 0`은 반복문 밖에서 한 번만 실행되어야 한다. 반복문 안에 있으면 숫자를 더할 때마다 합계가 다시 0으로 초기화된다.

최솟값과 최댓값처럼 값 두 개를 한 번에 반환할 수도 있다.

```python
def 최소최대(nums):
    return min(nums), max(nums)


최소, 최대 = 최소최대([3, 7, 1, 9])
```

`min()`과 `max()`는 파이썬이 기본으로 제공하는 내장 함수다. 반면 `append()`는 리스트 뒤에 `.`을 붙여 호출하는 리스트 메서드다.

## 예외 처리로 0 나누기 막기

0으로 나누면 `ZeroDivisionError`가 발생한다. 이 경우 `try`와 `except`로 오류를 처리할 수 있다.

```python
def 안전나눗셈(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return None
```

성공했을 때는 `try` 안에서 계산 결과를 반환하고, 0으로 나눴을 때는 `except` 안에서 `None`을 반환한다. 두 경우 모두 `return`이 있으므로 함수 마지막에 별도의 `return`은 필요 없다.

## 클래스, 객체, 그리고 `self`

클래스는 객체를 만들기 위한 설계도이고, 객체는 설계도로 만든 실제 대상이다.

```python
class 사람:
    pass


사람1 = 사람()
사람1.이름 = "유나"

print(사람1.이름)
```

객체를 만들면서 값을 전달하려면 `__init__`을 사용할 수 있다.

```python
class 학생:
    def __init__(self, 이름, 나이):
        self.이름 = 이름
        self.나이 = 나이
```

```python
학생1 = 학생("김민수", 24)
```

`self`는 현재 생성하거나 사용 중인 객체를 가리키는 참조다. `self.이름 = 이름`에서 오른쪽 `이름`은 함수에 전달된 매개변수이고, 왼쪽 `self.이름`은 현재 객체 안에 저장되는 속성이다.

객체 내부에 저장된 값은 메서드에서 다시 사용할 수 있다.

```python
class 학생:
    def __init__(self, 이름, 나이):
        self.이름 = 이름
        self.나이 = 나이

    def introduce(self):
        print(f"{self.이름}입니다. {self.나이}살이에요.")


학생1 = 학생("김민수", 24)
학생1.introduce()
```

`학생1.introduce()`를 호출하면 파이썬이 현재 객체인 `학생1`을 `self`로 자동 전달한다. 따라서 메서드에 이름과 나이를 다시 전달하지 않아도 객체에 저장된 정보를 사용할 수 있다.

## 마무리

오늘 학습의 핵심은 다음과 같다.

- 파일은 `write()`로 작성하며, `"w"`와 `"a"` 모드를 목적에 맞게 선택한다.
- `append()`는 리스트에, `write()`는 파일에 사용한다.
- `return`은 계산 결과를 함수 밖으로 전달하며, 여러 값도 반환할 수 있다.
- 예상 가능한 오류는 필요한 예외 유형만 지정해 처리한다.
- 클래스는 설계도, 객체는 실제 대상이며, `self`는 현재 객체를 가리킨다.
