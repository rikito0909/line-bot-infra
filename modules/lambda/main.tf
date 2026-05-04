resource "aws_lambda_function" "this" {
  role          = aws_iam_role.lambda_role.arn
  function_name = "line-bot-dev"
  filename      = "./lambda_src/lambda_function.py.zip"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.14"

  timeout     = 20
  memory_size = 128

  # Parameter Store想定
  # environment {
  # }

  depends_on = [aws_cloudwatch_log_group.this]

  tags = {
    Name         = "${var.project_name}-${var.environment}-lambda"
    project_name = var.project_name
    environment  = var.environment
  }
}

#===============================
# IAM
#===============================
resource "aws_iam_role" "lambda_role" {
  name = "lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "lambda_dynamodb_policy" {
  name = "lambda-dynamodb-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ]
        Resource = var.dynamodb_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_dynamodb_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

#===============================
# cloudwatch
#===============================
# Lambda のロググループを明示的に作成し、ログ保持期間を Terraform で管理する。
# 事前に作成しない場合、Lambda 初回実行時にデフォルト設定で自動作成される。
# ==========================================
resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/lambda/${aws_lambda_function.this.function_name}"
  retention_in_days = 7
}
