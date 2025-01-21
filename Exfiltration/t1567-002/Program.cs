using System;
using Amazon.S3;
using Amazon.S3.Transfer;
using Amazon;
using System.Threading.Tasks;
using System.IO;

class Program
{
    private const string accessKey = "your-access-key";
    private const string secretKey = "your-secret-key";
    private static readonly RegionEndpoint defaultBucketRegion = RegionEndpoint.USEast1;

    static void Main(string[] args)
    {
        if (args.Length < 3 || args.Length > 4)
        {
            var binaryName = AppDomain.CurrentDomain.FriendlyName;
            Console.WriteLine($"Usage: {binaryName} <upload/download> <file_path> <bucket_name> [region]");
            return;
        }

        var operation = args[0];
        var filePath = args[1];
        var bucketName = args[2];
        var bucketRegion = args.Length == 4 ? RegionEndpoint.GetBySystemName(args[3]) : defaultBucketRegion;

        try
        {
            var s3Client = new AmazonS3Client(accessKey, secretKey, bucketRegion);
            if (operation.ToLower() == "upload")
            {
                UploadFileAsync(s3Client, filePath, bucketName).Wait();
            }
            else if (operation.ToLower() == "download")
            {
                DownloadFileAsync(s3Client, filePath, bucketName).Wait();
            }
            else
            {
                Console.WriteLine("Invalid operation. Use 'upload' or 'download'.");
            }
        }
        catch (Exception e)
        {
            Console.WriteLine($"Error encountered on server. Message:'{e.Message}'");
        }
    }

    private static async Task UploadFileAsync(IAmazonS3 client, string filePath, string bucketName)
    {
        try
        {
            var fileTransferUtility = new TransferUtility(client);
            await fileTransferUtility.UploadAsync(filePath, bucketName);
            Console.WriteLine($"Upload completed: {filePath}");
        }
        catch (AmazonS3Exception e)
        {
            Console.WriteLine($"Error encountered on server. Message:'{e.Message}'");
        }
        catch (Exception e)
        {
            Console.WriteLine($"Unknown error encountered on server. Message:'{e.Message}'");
        }
    }

    private static async Task DownloadFileAsync(IAmazonS3 client, string filePath, string bucketName)
    {
        try
        {
            var fileTransferUtility = new TransferUtility(client);
            var downloadFilePath = Path.Combine(Directory.GetCurrentDirectory(), filePath);
            await fileTransferUtility.DownloadAsync(downloadFilePath, bucketName, filePath);
            Console.WriteLine($"Download completed: {downloadFilePath}");
        }
        catch (AmazonS3Exception e)
        {
            Console.WriteLine($"Error encountered on server. Message:'{e.Message}'");
        }
        catch (Exception e)
        {
            Console.WriteLine($"Unknown error encountered on server. Message:'{e.Message}'");
        }
    }
}

