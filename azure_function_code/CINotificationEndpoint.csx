#r "Newtonsoft.Json"
#r "Microsoft.WindowsAzure.Storage"

using System;
using System.Collections.Generic;
using System.Collections.Specialized;
using System.Net;
using System.Text;
using System.Text.RegularExpressions;

using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Primitives;
using Newtonsoft.Json;
using Microsoft.WindowsAzure.Storage;
using Microsoft.WindowsAzure.Storage.Blob;

public static async Task<IActionResult> Run(HttpRequest req, ILogger log)
{
    log.LogInformation("C# HTTP trigger function processed a request.");

    string requestBody = await new StreamReader(req.Body).ReadToEndAsync();
    if (req.ContentType == "application/x-www-form-urlencoded") {
        string query = System.Web.HttpUtility.UrlDecode(requestBody);
        NameValueCollection result = System.Web.HttpUtility.ParseQueryString(query);
        requestBody = result["payload"];
    }
    dynamic data = JsonConvert.DeserializeObject(requestBody);

    // Check if the build is what we want to record
    // Builds to be recorded:
    //     1. seed branch as baseline;
    //     2. tool_seed branch to make sure the tool doesn't break the build;
    //     3. second build of tool_commit_increment branch to check the effect of the tool
    string branch = data.branch;

    string message = data.message;
    string commit = data.commit;
    log.LogInformation($"Received commit {commit}: {message} from {branch}");

    // Define a regular expression for seed branches and increment branch.
    Regex seed = new Regex(@".*seed_(?<recent_k>\d+)$", RegexOptions.Compiled | RegexOptions.IgnoreCase);
    Regex increment = new Regex(@"(?<tool_name>\w+)_\d+-(?<recent_k>\d+)$", RegexOptions.Compiled | RegexOptions.IgnoreCase);
    // Find matches.
    MatchCollection matches = increment.Matches(branch);
    if (matches.Count == 0) {
        matches = seed.Matches(branch);
    } else {
        // if it is the branch to be incremented (simulate one development commit), then send out a merge request
        string owner = data.repository.owner_name;
        string repo = data.repository.name;
        string targetUrl = $"https://api.github.com/repos/{owner}/{repo}/merges?access_token=d3fee1f259eef562b1cec203c9a47e95cd4ced97";

        GroupCollection matchGroups = matches.ElementAt(0).Groups;
        string tag = matchGroups.ElementAt(1).Value;
        string idx = matchGroups.ElementAt(2).Value;

        Dictionary<string, string> mergeRequestDict = new Dictionary<string, string>();
        mergeRequestDict.Add("base", $"{branch}");
        mergeRequestDict.Add("head", $"{tag}_seed_{idx}");
        mergeRequestDict.Add("commit_message", $"Increment to recent {idx} commit");

        string mergeRequest = JsonConvert.SerializeObject(mergeRequestDict);
        var stringContent = new StringContent(mergeRequest, UnicodeEncoding.UTF8, "application/json");
        
        var client = new HttpClient();
        client.DefaultRequestHeaders.Add("User-Agent", "CIReinteract");
        var response = await client.PostAsync(targetUrl, stringContent);
        var result = await response.Content.ReadAsStringAsync();
        if (response.StatusCode == HttpStatusCode.Created) {
            log.LogInformation($"Trigger commit incrementation on branch {branch}");
            return new OkObjectResult("Reinteraction triggered");
        } else if (response.StatusCode != HttpStatusCode.NoContent) {
            log.LogInformation($"Unexpected status code on incrementing commit: {response.StatusCode}: {result}");
            return new BadRequestObjectResult("Unexpected error on incrementing commit");
        }
    }
    if (matches.Count == 0) {
        return new OkObjectResult($"Build for {branch} branch will not be recorded");
    }

    // Get Travis job detail and log them into files, each build can contain multiple jobs
    string storageConnectionString = Environment.GetEnvironmentVariable("STORAGE_CONNECTION");
    CloudStorageAccount storageAccount;

    // Check whether the connection string can be parsed.
    if (CloudStorageAccount.TryParse(storageConnectionString, out storageAccount))
    {
        // If the connection string is valid, proceed with operations against Blob storage here.
        // Create the CloudBlobClient that represents the Blob storage endpoint for the storage account.
        CloudBlobClient cloudBlobClient = storageAccount.CreateCloudBlobClient();
        CloudBlobContainer cloudBlobContainer = cloudBlobClient.GetContainerReference("test-reports");

        string logString = "";
        foreach (dynamic jobDetail in data.matrix) {
            string jobId = jobDetail.id;
            string jobState = jobDetail.state;
            string start = jobDetail.started_at;
            string end = jobDetail.finished_at;
            DateTime jobStart = DateTime.Parse(start);
            DateTime jobEnd = DateTime.Parse(end);
            double timeElapsedSec = (jobEnd - jobStart).TotalSeconds;
            
            // Not collecting log here because log is used to identify reasons of possible failures
            // and run time for tests.
            // However, in this application, we only care:
            //   1. if the job state is consistent for the specific commit (reasons don't matter)
            //   2. the total time for the job
            //      (test time is not the primary concern as developers only get feedback when the job is finished)
            // What's more, a more detail results about tests being executed is not contained in log.txt
            // For projects that use surefire, the surefire report is what we need and be stored by other Azure function endpoint.
            logString += $"Finished abstracting data: id {jobId}; state {jobState}; time {timeElapsedSec}\n";
            log.LogInformation(logString);
        }
        string logFileName = $"{branch}.txt";
        // Get a reference to the blob address, then upload the file to the blob.
        // Use the value of localFileName for the blob name.
        CloudBlockBlob cloudBlockBlob = cloudBlobContainer.GetBlockBlobReference(logFileName);
        using (var stream = new MemoryStream(Encoding.Default.GetBytes(logString), false))
        {
            await cloudBlockBlob.UploadFromStreamAsync(stream);
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