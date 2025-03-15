import boto3
import sys

def upload_to_s3(access_key, secret_key, region, bucket_name, file_path):
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        file_name = file_path.split("\\")[-1]
        print(f"Uploading {file_path} to bucket {bucket_name}")
        s3_client.upload_file(file_path, bucket_name, file_name)
        print(f"File '{file_name}' uploaded to bucket '{bucket_name}' successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
  if len(sys.argv) != 3:
    print("Usage: .\t1567-002.exe <bucketname> <filepath>")
    sys.exit(1)

  accessKey = "your-access-key"
  secretKey = "your-secret-key"
  region = "your-aws-region"
  bucket_name = sys.argv[1]
  file_path = sys.argv[2]
  upload_to_s3(accessKey, secretKey, region, bucket_name, file_path)
