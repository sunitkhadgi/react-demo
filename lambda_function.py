import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Products')


def decimal_default(obj):
    """Helper to serialize Decimal types returned by DynamoDB."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError


def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'  # enable CORS for API Gateway testing
        },
        'body': json.dumps(body, default=decimal_default)
    }


def lambda_handler(event, context):
    print("EVENT RECEIVED:", event)

    http_method = event.get('httpMethod', '')
    path_params = event.get('pathParameters') or {}
    product_id = path_params.get('productId')

    # Safely parse body (handles both API Gateway and direct test invokes)
    body = event.get('body')
    if body:
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return response(400, {"error": "Invalid JSON in request body"})
    else:
        data = event  # fallback for direct test invocation without 'body'

    try:
        # ---------- CREATE ----------
        if http_method == 'POST':
            products = data.get('products')

            # support single product creation too
            if not products and 'productId' in data:
                products = [data]

            if not products:
                return response(400, {"error": "No products provided"})

            with table.batch_writer() as batch:
                for product in products:
                    batch.put_item(Item=product)

            return response(200, {"message": f"{len(products)} products inserted"})

        # ---------- READ ----------
        elif http_method == 'GET':
            if product_id:
                result = table.get_item(Key={'productId': product_id})
                item = result.get('Item')
                if not item:
                    return response(404, {"error": "Product not found"})
                return response(200, item)
            else:
                result = table.scan()
                items = result.get('Items', [])
                return response(200, {"count": len(items), "products": items})

        # ---------- UPDATE ----------
        elif http_method == 'PUT':
            if not product_id:
                return response(400, {"error": "productId is required in path"})

            update_fields = {k: v for k, v in data.items() if k != 'productId'}
            if not update_fields:
                return response(400, {"error": "No fields to update"})

            update_expr = "SET " + ", ".join(f"#{k} = :{k}" for k in update_fields)
            expr_attr_names = {f"#{k}": k for k in update_fields}
            expr_attr_values = {f":{k}": v for k, v in update_fields.items()}

            table.update_item(
                Key={'productId': product_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values
            )

            return response(200, {"message": f"Product {product_id} updated successfully"})

        # ---------- DELETE ----------
        elif http_method == 'DELETE':
            if product_id:
                # single delete via path param
                table.delete_item(Key={'productId': product_id})
                return response(200, {"message": f"Product {product_id} deleted successfully"})

            # batch delete via body
            product_ids = data.get('productIds', [])
            if not product_ids:
                return response(400, {"error": "No productIds provided"})

            with table.batch_writer() as batch:
                for pid in product_ids:
                    batch.delete_item(Key={"productId": pid})

            return response(200, {"message": f"{len(product_ids)} products deleted successfully"})

        else:
            return response(405, {"error": f"Method {http_method} not allowed"})

    except Exception as e:
        print("ERROR:", str(e))
        return response(500, {"error": str(e)})
