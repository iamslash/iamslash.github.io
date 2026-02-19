# iamslash.github.io

[mdBook](https://rust-lang.github.io/mdBook/)으로 만든 개인 사이트.

## 로컬 개발

```bash
# mdBook 설치
cargo install mdbook

# 로컬 서버 실행 (http://localhost:3000)
mdbook serve

# 빌드만 실행
mdbook build
```

## 콘텐츠 추가

1. `src/` 디렉토리에 마크다운 파일 생성
2. `src/SUMMARY.md`에 해당 파일 링크 추가

```markdown
# Summary

- [About](./about.md)
- [새 페이지](./new-page.md)
```

## 배포

`main` 브랜치에 push하면 GitHub Actions가 자동으로 빌드 및 배포한다.

## 디렉토리 구조

```
.
├── book.toml          # mdBook 설정
├── src/
│   ├── SUMMARY.md     # 목차 (사이드바)
│   └── about.md       # 콘텐츠 페이지
├── book/              # 빌드 출력 (gitignore)
└── .github/workflows/ # CI/CD
```
