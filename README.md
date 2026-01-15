# Stack Bot

사용자 프로필 및 서버 관리를 위한 Discord Bot입니다.

## 기능

- **프로필 관리**: 유저 프로필 등록 및 조회
- **관리자 기능**: 경고 관리, 메모 작성, 메시지 청소
- **로그 시스템**: 서버 이벤트 자동 로그 (입장/퇴장, 메시지 수정/삭제)
- **역할 반응**: 메시지에 반응하여 자동으로 역할 지급/회수

## 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
# .env 파일에 DISCORD_TOKEN 설정
DISCORD_TOKEN=your_bot_token_here
```

## 실행

```bash
python main.py
```

## 프로젝트 구조

```
stack/
├── main.py                 # 봇 메인 클래스
├── commands/               # 명령어 디렉토리 (1명령어 1파일)
│   ├── profile.py         # 프로필 명령어
│   ├── add_warning.py     # 경고 추가
│   ├── remove_warning.py  # 경고 제거
│   ├── memo.py            # 메모 작성
│   ├── log_channel.py     # 로그 채널 설정
│   ├── clear.py           # 메시지 청소
│   ├── event_logger.py    # 이벤트 로거
│   └── reaction/          # 반응 역할 그룹
│       ├── __init__.py    # 패키지 초기화 (명령어 없음)
│       ├── message_setup.py  # /반응 메시지생성
│       ├── add.py         # /반응 설정
│       ├── list.py        # /반응 목록
│       └── remove.py      # /반응 제거
├── utils/                  # 유틸리티
│   ├── constants.py       # 상수 정의
│   ├── data_manager.py    # 데이터 관리 (SQLite)
│   ├── extension_loader.py # 명령어 로더
│   ├── logging_config.py  # 로깅 설정
│   └── graceful_shutdown.py # 안전한 종료
└── data/                   # 데이터 저장소
    └── stack_bot.db       # SQLite 데이터베이스
```

## 명령어

### 프로필 관련
- `/프로필등록` - 프로필 등록/수정
- `/프로필목록` - 등록된 프로필 목록 조회
- `/정보` - 유저 프로필 정보 조회

### 관리자 전용
- `/경고추가` - 경고 추가
- `/경고제거` - 경고 제거
- `/메모작성` - 관리자 메모 작성
- `/로그채널설정` - 로그 채널 설정
- `/청소` - 메시지 삭제

### 역할 반응 (관리자 전용)
- `/반응 메시지생성` - 역할 인증 메시지 생성
- `/반응 설정` - 메시지에 반응 역할 설정
- `/반응 목록` - 설정된 반응 역할 목록 조회
- `/반응 제거` - 반응 역할 설정 제거

## 요구사항

- Python 3.10+
- py-cord 2.6.0+
- aiosqlite 0.19.0+
- python-dotenv 1.0.0+

## 라이선스

MIT License
