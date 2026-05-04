# LINE Bot サーバーレス構成（Terraform）

## 概要

本プロジェクトは、Terraformを用いてLINE Botのためのサーバーレス構成を構築するものです。

LINE Messaging APIからのWebhookリクエストを受け取り、AWS Lambdaで処理し、ユーザーデータをDynamoDBに保存します。

---

## 構成

API Gateway → Lambda → DynamoDB

* **API Gateway**: LINEからのWebhookリクエストを受信
* **Lambda**: メッセージ処理・ビジネスロジック実行
* **DynamoDB**: ユーザーデータおよび履歴の保存
* **CloudWatch Logs**: ログ管理（保持期間：7日）

---

## この構成を採用した理由

* サーバーレス構成により運用負荷を最小化
* DynamoDBによりスケーラブルなデータ管理を実現
* マネージドサービス中心にすることでインフラ管理コストを削減

---

## 使用技術

Terraformにより以下のリソースを構築しています：

* API Gateway（HTTP API）
* AWS Lambda
* DynamoDB
* CloudWatch Log Group（ログ保持期間のみを明示設定）
* IAMロール / ポリシー

---

## セキュリティ

* APIキーやトークンなどの機密情報はリポジトリに含めていません
* 環境変数またはAWS Systems Manager Parameter Storeで管理する前提です

---

## 補足

* LambdaのロググループはTerraformで明示的に作成し、ログ保持期間を管理しています
* デフォルトで自動生成されるロググループは使用していません

---

## 作者

いちかわ
