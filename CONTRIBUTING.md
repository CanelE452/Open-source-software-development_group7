# 팀 협업 안내

## 담당 파일부터 시작하기

[구조와 역할](docs/architecture.md), [API 계약](docs/api-contract.md), [개발 순서](docs/roadmap.md)를 확인합니다. 하나의 기능을 Issue 하나로 등록하고 담당자와 완료 조건을 적습니다. 자기 모듈 안에서 먼저 구현하고 공유 API·의존성·설정 변경은 관련 담당자와 조율합니다.

담당은 김민재(DB·검색), 신은지(API·수집), 김민수(분석·요약), 김서현(프런트)입니다.

## 커밋 작성자 확인

기여 이력을 정확하게 남기기 위해 커밋 전에 본인 이름과 GitHub 계정에 연결된 이메일이 설정되어 있는지 확인합니다.

```bash
git config --get user.name
git config --get user.email
```

값이 잘못되어 있다면 본인이 이 저장소에만 설정합니다. 이메일은 GitHub에 등록·확인된 주소 또는 본인의 GitHub noreply 주소를 사용하세요.

```bash
git config --local user.name "본인 이름"
git config --local user.email "본인 GitHub 이메일"
```

작업 내용과 담당자는 Issue와 PR에 기록합니다. 이메일 설정에 관한 자세한 내용은 [GitHub 커밋 이메일 안내](https://docs.github.com/en/account-and-profile/how-tos/email-preferences/setting-your-commit-email-address)를 참고하세요.

## 첫 업로드 담당자

초기 구조를 처음 업로드할 때 사용하는 절차입니다. 로컬 기본 브랜치가 `master`인 경우 `main`으로 변경합니다. 이미 `main`이면 브랜치 변경 명령을 생략합니다. 변경 파일을 확인한 뒤 필요한 경로를 지정해 스테이징합니다.

```bash
git status --short
git branch -m main
git add README.md CONTRIBUTING.md CHANGELOG.md LICENSE NOTICE .gitignore .gitattributes .editorconfig .python-version .env.example pytest.ini
git add backend frontend docs evaluation data .github
git diff --cached --stat
git diff --cached
git commit -m "chore: initialize team project structure"
git log -1 --format=fuller
git push -u origin main
```

커밋 전에 `git diff --cached`로 변경 내용을 검토합니다. `.env`, 로컬 DB, 가상환경, 모델 파일, `node_modules` 등은 `.gitignore`로 관리하며 저장소에 포함하지 않습니다.

## 기능 개발 순서

첫 업로드 이후 다른 팀원은 저장소를 clone합니다. 기존 로컬 폴더를 쓰는 사람은 작업 상태를 먼저 확인하고 `main`을 받아옵니다.

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/issue-collection
```

기능별로 브랜치를 만들고 구현·검증 후 변경 파일만 스테이징합니다.

```bash
git add backend/app/collection/github_issues.py backend/tests/test_collection.py
git commit -m "feat: collect repository issues"
git push -u origin feat/issue-collection
```

위 경로는 기능 구현 후 생성할 파일의 예시입니다. 커밋 접두사는 `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`를 사용합니다. PR에 관련 Issue와 검증 결과를 적고, 팀원 1명 이상 리뷰와 CI 통과 후 병합합니다. `CODEOWNERS`는 자동 리뷰 요청을 돕지만 필수 리뷰를 강제하지는 않습니다. `main` 보호와 필수 CI 설정은 저장소 관리자가 GitHub에서 별도로 설정합니다.

## 검증과 공유 파일

- 백엔드 변경: 루트에서 `python -m pytest -q` (가상환경 Python 사용).
- 프런트 변경: `npm --prefix frontend run typecheck`, `npm --prefix frontend run build`.
- API 변경: `docs/api-contract.md`, 백엔드 스키마, 프런트 타입을 함께 확인.
- Python 의존성 변경: `backend/requirements*.txt`와 설치 안내 검토.
- npm 의존성 변경: `package.json`과 `package-lock.json`을 함께 변경. 다른 팀원은 `npm ci` 사용.
- 평가: 질의·관련성 판정과 원문 스냅샷 버전/해시를 기록. 실행 결과를 덮어써 비교 근거를 잃지 않기.

회의에서 정한 내용과 다음 작업은 `docs/meetings/YYYY-MM-DD.md`에 적습니다.
