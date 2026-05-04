module "lambda" {
  source = "../../modules/lambda"

  environment  = var.environment
  project_name = var.project_name
  dynamodb_arn = module.dynamodb.dynamodb_arn
}

module "dynamodb" {
  source = "../../modules/dynamodb"

  environment  = var.environment
  project_name = var.project_name
}

module "cloudwatch" {
  source = "../../modules/cloudwatch"

  environment  = var.environment
  project_name = var.project_name
  aws_lambda_function_function_name = module.lambda.aws_lambda_function_function_name
}

module "apigateway" {
  source = "../../modules/apigateway"

  environment  = var.environment
  project_name = var.project_name
  aws_lambda_function_invoke_arn = module.lambda.aws_lambda_function_invoke_arn
  aws_lambda_function_function_name = module.lambda.aws_lambda_function_function_name
}