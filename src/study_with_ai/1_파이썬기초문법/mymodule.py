def greeting_module(name):
    """
    인사하는 함수
    전달받은 이름을 사용하여 인사를 반환한다

    """
    return f"{name}님 안뇽"


def test(age):
    """ 나이를 출력하는 함수"""

    return f"나이가 {age} 이네용"


def total_expenses1(*amounts):

    교통비=10
    세금=5
    통신비=6
    생활비=7
    월세=8
    
    if True :
       expenses=교통비+세금+통신비+생활비+월세 
       return expenses

def total_expenses(**expenses):

    total = 0 # 지역변수를 사용해서 함수값과 다르게 지정
    for category,amount in expenses.items():
        print(f"{category}: {amount,}원")
        total+=amount
         
    return (f"{total:,}원")

def check_budget(budget,**expense):
    총지출=0
    예산=budget
    
    for 항목, 금액 in expense.items():
        print(f"{항목}:{금액:,}원")
        총지출+=금액
    print("---"*10)

    결과 = 예산 - 총지출
    if 결과 >0:
        print("예산이 남아있습니다")
    else :
        print("예산이 초과하였습니다")

    return print(f"총 예산: {결과}")


    
    


        


