---
title: docusaurus, netlify, netlify cms usages
slug: build-deploy-docusaurus
authors: [iamslash]
tags: [docusaurus, netlify, netlify cms]
---
# docusaurus 를 build & deploy 하기

```bash
// Deploy on local
$ yarn start
```

# docusaurus 를 netlify CMS 와 연동하기

[Docusaurus | netlify CMS](https://www.netlifycms.org/docs/docusaurus/)

# netlify CMS 로 글을 쓰기

[iamslash.netlify.app/admin](iamslash.netlify.app/admin) 으로 접속한다. 글을 쓴다. Publish now 한다. 자동으로 배포된다. [iamslash.netlify.app](iamslash.netlify.app) 으로 접속한다.

# GitHub 에서 docusaurus 를 deploy 하기

```
$ npm install gh-pages -g
$ gh-pages -d build
```