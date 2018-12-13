#r "Newtonsoft.Json"
#r "Microsoft.WindowsAzure.Storage"

using System.Net;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Primitives;
using Newtonsoft.Json;
using Microsoft.WindowsAzure.Storage;
using Microsoft.WindowsAzure.Storage.Blob;

public static async Task<IActionResult> Run(HttpRequest req, ILogger log)
{
    string storageConnectionString = Environment.GetEnvironmentVariable("STORAGE_CONNECTION");

    log.LogInformation(storageConnectionString);

    CloudStorageAccount storageAccount;

    // Check whether the connection string can be parsed.
    if (CloudStorageAccount.TryParse(storageConnectionString, out storageAccount))
    {
        // If the connection string is valid, proceed with operations against Blob storage here.
        // Create the CloudBlobClient that represents the Blob storage endpoint for the storage account.
        CloudBlobClient cloudBlobClient = storageAccount.CreateCloudBlobClient();
        CloudBlobContainer cloudBlobContainer = cloudBlobClient.GetContainerReference("test-reports");

        var formData = await req.ReadFormAsync();
        var fileCollection = formData.Files;

        foreach (dynamic uploadedFile in fileCollection) {
            log.LogInformation($"{uploadedFile.Name}");
            // Get a reference to the blob address, then upload the file to the blob.
            // Use the value of localFileName for the blob name.
            CloudBlockBlob cloudBlockBlob = cloudBlobContainer.GetBlockBlobReference(uploadedFile.FileName);
            await cloudBlockBlob.UploadFromStreamAsync(uploadedFile.OpenReadStream());
        }
    }
    else
    {
        // Otherwise, let the user know that they need to define the environment variable.
        log.LogError(
            "A connection string has not been defined in the system environment variables. " +
            "Add a environment variable named 'storageconnectionstring' with your storage " +
            "connection string as a value.");
        log.LogError("Press any key to exit the sample application.");
    }

    return new OkObjectResult("Message Received");
}