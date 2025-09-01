"""
==========================================
파일명   : env_logging_example/main.py
목적     : python-dotenv와 logging 모듈을 활용한
          .env 환경 변수 로드 및 로그 출력 실습
작성자   : 고나연
작성일   : 2025-08-12
버전     : Python 3.11 기준
설명     :
    본 프로그램은 .env 파일에서 로그 레벨과 앱 이름을 읽어와
    logging 모듈을 통해 로그를 콘솔과 파일(app.log) 양쪽에 출력합니다.
    로그 포맷은 "시간 [레벨] 메시지" 형태이며,
    로그 레벨은 .env의 LOG_LEVEL 값에 따라 동적으로 설정됩니다.

    주요 기능:
    1. python-dotenv를 사용한 .env 파일 로드
    2. os.getenv()로 환경 변수 읽기
    3. logging.basicConfig를 이용한 로그 설정
       - 로그 파일명: app.log
       - 로그 레벨: .env에서 읽은 값 적용
       - 로그 포맷: 시간 [레벨] 메시지
       - 로그 출력: 콘솔 + 파일 핸들러 동시 구성
    4. INFO, DEBUG, ERROR 레벨 로그 메시지 출력
       - ERROR 로그는 ZeroDivisionError 예외 발생 시 기록

변경이력 :
    2025-08-12 : 최초 작성 및 테스트 완료

참고     :
    - python-dotenv 모듈 사용법
    - logging 모듈 핸들러 다중 구성 방법
    - .env 파일 활용한 환경 변수 관리
==========================================
"""

import os
import logging
from dotenv import load_dotenv

# .env 로드
# load_dotenv; .env 파일을 로드하는 함수
load_dotenv(dotenv_path=".env")

# 환경변수 읽기
# 환경 변수에서 LOG_LEVEL 값을 읽어오고 대문자로 변환, 기본값은 "INFO"
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
app_name = os.getenv("APP_NAME", "MyApp")

# 로그 레벨 매핑
level_dict = {
"DEBUG": logging.DEBUG,
"INFO": logging.INFO,
"WARNING": logging.WARNING,
"ERROR": logging.ERROR,
"CRITICAL": logging.CRITICAL,
}
log_level = level_dict.get(log_level_str, logging.INFO)

# 로깅 설정
# 시간 [로그레벨] 메시지 형태
log_format = "%(asctime)s [%(levelname)s] %(message)s"
log_file_path = "app.log"

#기존 핸들러 초기화 후 로그 레벨 재설정
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# logging.basicConfig()로 로깅 설정
# level: 로그 레벨 설정
# format: 로그 출력 포맷 지정
# handlers: 로그를 출력할 핸들러 리스트 (콘솔, 파일 모두 출력)
logging.basicConfig(
    level=log_level,
    format=log_format,
    handlers=[
        logging.StreamHandler(),  # 콘솔 출력
        logging.FileHandler(log_file_path, encoding="utf-8")  # 파일 출력
    ]
)

# 로그 메시지 출력
# 앱 실행 시작을 INFO 레벨 로그로 출력 (app_name 포함)
logging.info(f"[INFO] {app_name} 앱 실행 시작")
# 환경 변수 로딩 완료를 DEBUG 레벨 로그로 출력
logging.debug(f"[DEBUG] 환경 변수 로딩 완료")


try:
    1 / 0   # 의도적으로 0으로 나누어 예외 발생
except ZeroDivisionError:
    # ZeroDivisionError 예외 발생 시 ERROR 레벨 로그 출력
    logging.error("[ERROR] 예외 발생: 0으로 나눌 수 없습니다.")