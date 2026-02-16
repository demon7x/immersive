# immersive

ZED2 헤드 트래킹 기반 anamorphic inward-box MVP 앱입니다.

## 스택
- Ubuntu 22.04
- Python 3.10+
- PyQt6 + OpenGL
- ZED SDK Python bindings (`pyzed.sl`)

## 실행
```bash
./scripts/run.sh
```

`pyzed.sl`이 설치되지 않았거나 ZED2 카메라가 연결되지 않으면 앱 시작 시 오류를 출력하고 종료합니다.

ZED2 없이 렌더링만 테스트하려면:
```bash
./scripts/run.sh --input-mode keyboard
```

Colab/헤드리스에서 파일 렌더 테스트:
```bash
python -m app.colab_render --duration-s 4 --fps 24 --width 960 --height 540 --format mp4 --path-type orbit --out outputs/colab_render.mp4
```

## 프로젝트 구조
- `app/main.py`: 앱 엔트리포인트
- `app/tracking/zed_tracker.py`: ZED Body Tracking 기반 헤드 포즈 추출
- `app/tracking/keyboard_tracker.py`: 방향키 기반 가상 헤드 포즈 추출
- `app/tracking/pose_filter.py`: EMA + 속도 제한 + 추적 손실 복귀 정책
- `app/calibration/display_calibrator.py`: 뷰/투영 행렬 계산
- `app/render/gl_widget.py`: inward-box OpenGL 렌더러
- `app/render/headless_matplotlib.py`: Colab용 headless 렌더러
- `app/colab_render.py`: Colab/CLI 렌더 시퀀스 생성 엔트리포인트
- `app/sim/camera_path.py`: 스크립트 기반 카메라 경로 생성
- `app/ui/control_panel.py`: Start/Stop, Recalibrate, FOV/Depth UI
- `app/config/defaults.yaml`: 기본 설정
- `app/config/runtime.yaml`: 저장된 사용자 캘리브레이션(앱에서 Save Calibration 클릭 시 생성)
- `tests/unit/`: 필터/캘리브레이터 단위 테스트
- `tests/integration/`: 설정-파이프라인 계약 테스트

## 테스트
```bash
python3 -m pytest -q
```

## 캘리브레이션 저장
- 우측 패널의 `Save Calibration` 버튼을 누르면 `app/config/runtime.yaml`에 현재 설정(FOV/Depth 포함)이 저장됩니다.
- 다음 실행부터 `runtime.yaml`이 있으면 기본값 대신 우선 로드됩니다.
- 하단 상태바에서 실시간 `FPS`와 추정 `Latency`를 확인할 수 있습니다.

## 키보드 테스트 모드 조작
- `Left` / `Right`: X 축 이동
- `Up` / `Down`: Y 축 이동
- 키를 누르고 있는 동안 연속 이동
- 창 포커스를 잃으면 입력 상태는 자동으로 초기화됩니다.

## Colab 테스트
- `notebooks/colab_render_test.ipynb` 노트북을 사용하면 Colab에서 MP4/GIF를 생성해 바로 미리볼 수 있습니다.
- 기본 경로는 `outputs/colab_render.mp4`이며, MP4 인코딩 실패 시 GIF로 폴백됩니다.
