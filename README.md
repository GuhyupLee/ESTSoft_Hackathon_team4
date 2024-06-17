# 이스트소프트 제 1회 해커톤 4팀

<div align="center">
<img width="329" alt="image" src="https://github.com/GuhyupLee/ESTSoft_Hackathon_team4/assets/160453988/4889b551-2aba-41dc-b597-018ba9513fdc">
</div>

# 외로운 일상의 소중한 기억을 지켜주는 플랫폼 "기억나래"
> **해커톤 기간: 2024.06.14 ~ 2024.06.16**

## 개발팀 소개

|      팀장     |         개발         |       기획      |
| :------------------------------------------------------------------------------: | :---------------------------------------------------------------------------------------------------------------------------------------------------: |  :---------------------------------------------------------------------------------------------------------------------------------------------------: | 
|      이구협      |         박태우         |       신혜선      |
|   [@GuhyupLee](https://github.com/GuhyupLee)   |    [@taewoosuin](https://github.com/taewoosuin)  | [@nyedong](https://github.com/nyedong)  |
| STT-TTS 모델 개발, 인지능력검사 구현 | UI/UX 개선, 챗봇 및 그림일기 구현 | 프로젝트 관리, 기능명세서 작성 |

|      기획     |         개발         |       개발     |
| :------------------------------------------------------------------------------: | :---------------------------------------------------------------------------------------------------------------------------------------------------: |  :---------------------------------------------------------------------------------------------------------------------------------------------------: |
|         원수림         |         정강빈         |         최재형         |
| [@surimwon](https://github.com/surimwon)  | [@bigdefence](https://github.com/bigdefence)  | [@JaydenCJH](https://github.com/JaydenCJH)  |
| UI 기획, 와이어프레임 작성 | 보호자 페이지 구현, 로컬 모델 개발 시도 | 프롬프트 엔지니어링, 개발기획서 작성 |    


## 서비스 소개

기억나래는 노인 사용자의 일상을 기록하고 인지 기능을 모니터링하여 건강한 노후 생활을 지원하는 AI 기반 서비스입니다.

사용자는 모바일 앱을 통해 AI 챗봇과 음성 대화를 나누며, 이를 통해 일상이 자동으로 기록되고 그림일기 형태로 요약되어 제공됩니다. 또한, 음성 인터페이스를 통해 인지 기능 검사를 수행하고 결과를 사용자와 보호자에게 제공할 수 있습니다.

#### 주요기능

1.	STT-TTS 기술을 활용한 자연스러운 음성 대화
2.	프롬프트 엔지니어링을 통한 매끄러운 대화 경험
3.	일상 대화 내용의 자동 요약 및 그림일기 변환
4.	음성 기반 인지 기능 검사 시스템
5.	보호자용 모니터링 대시보드

#### 서비스 추친 배경

저출산 고령화로 인한 노인 부양의 사회적 부담이 증가하면서 치매를 비롯한 인지장애의 조기 발견과 예방이 중요해지고 있습니다. 

이를 해결하기 위해 우리 팀은 LLM 기반 실시간 음성 대화 서비스인 '기억나래'를 개발하기로 하였습니다
기억나래는 인지 기능 선별과 맞춤형 인지 훈련을 제공하며, 독거노인과 원거리 자녀 간의 소통 창구로도 활용될 예정입니다.

## Stacks

### Environment
<img alt="Visual Studio Code" src="https://img.shields.io/badge/VisualStudioCode-0078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white"/>
<img alt="GitHub" src="https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white"/>    

### Development

<img alt="Python" src="https://img.shields.io/badge/python-%2314354C.svg?style=for-the-badge&logo=python&logoColor=white"/>
<img alt="JavaScript" src="https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E"/>

### Communication
<img alt="Notion" src="https://img.shields.io/badge/Notion-%23000000.svg?style=for-the-badge&logo=notion&logoColor=white"/>
<img alt="Figma" src="https://img.shields.io/badge/figma-%23F24E1E.svg?style=for-the-badge&logo=figma&logoColor=white"/>
<img alt="Discord" src="https://img.shields.io/badge/%3CServer%3E-%237289DA.svg?style=for-the-badge&logo=discord&logoColor=white"/>

---
## 화면 구성 📺
| 메인 페이지  |  보호자 페이지   |
| :-------------------------------------------: | :-------------------------------------------: |
|  <img width="329" alt="image" src="https://github.com/GuhyupLee/ESTSoft_Hackathon_team4/assets/160453988/57502561-84bc-427a-9950-58e2b804f5cb"> |  <img width="329" alt="image" src="https://github.com/GuhyupLee/ESTSoft_Hackathon_team4/assets/160453988/70f36567-d87f-446b-be30-f2f60357d87f">    |  
| 대화 페이지   |  일기 페이지   |  
| <img width="329" alt="image" src="https://github.com/GuhyupLee/ESTSoft_Hackathon_team4/assets/160453988/4d14aab8-f378-45ca-8c1f-d2f0e07fe572">   |  <img width="329" alt="image" src="https://github.com/GuhyupLee/ESTSoft_Hackathon_team4/assets/160453988/4458c238-0711-4873-a8f0-a2a4f0e95e7c">     |
| 문제 풀이 페이지   |  문제 결과 페이지   |  
| <img width="329" alt="image" src="https://github.com/GuhyupLee/ESTSoft_Hackathon_team4/assets/160453988/d90e0602-f8f9-4679-8785-d92ba87c31d4">   |  <img width="329" alt="image" src="https://github.com/GuhyupLee/ESTSoft_Hackathon_team4/assets/160453988/493aef56-2dfa-4ce1-890e-4650ea2c61fe">     |

---
## 아키텍쳐

### 디렉토리 구조
```
├── .env
├── requirements.txt
├── run.py : 서버 실행 파일
└── app 
    ├── data : 대화 데이터 기록
    ├── guardian : 보호자 데이터 기록
    ├── users : 사용자 데이터 기록
    ├── static
    │   ├── css:
    │   │    └── style.css
    │   ├── images : 각종 이미지 
    │   └── js: 아래 세개만 js파일로 분리
    │       ├── congnitive_test.js : 인지능력 테스트 페이지 
    │       ├── congnitive_result.js : 인지능력 결과 페이지
    │       └── main_result.js : 보호자 확인용 인지능력 결과 페이지
    ├── templates
    |   ├── main.html
    |   ├── signup.html
    |   ├── login.html
    |   ├── select.html
    |   ├── chatbot.html
    |   ├── cognitive_test.html
    |   ├── select2.html
    |   ├── calender.html
    |   ├── record.html
    |   ├── select2.html
    |   ├── cognitive_result.html
    |   ├── guardian_main.html
    |   ├── guardian_signup.html
    |   ├── guardian_login.html
    │   └── guardian_cognitive_result.html
    ├── question.py
    ├── question_data.py
    ├── utils.py
    └── routes.py

```