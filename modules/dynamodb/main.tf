resource "aws_dynamodb_table" "this" {
  name         = "linebot-app-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "userId"
  range_key    = "sortKey"

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "sortKey"
    type = "S"
  }

  tags = {
    Name         = "${var.project_name}-${var.environment}-dynamodb"
    project_name = var.project_name
    environment  = var.environment
  }
}