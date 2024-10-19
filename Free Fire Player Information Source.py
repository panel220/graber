using Discord;
using Discord.WebSocket;
using Newtonsoft.Json;
using System;
using System.Net.Http;
using System.Threading.Tasks;

class Program
{
    private DiscordSocketClient _client;
    private static readonly string TOKEN = "YOUR_BOT_TOKEN"; 

    static async Task Main(string[] args) => await new Program().RunBotAsync();

    public async Task RunBotAsync()
    {
        var config = new DiscordSocketConfig
        {
            GatewayIntents = GatewayIntents.Guilds |
                             GatewayIntents.GuildMessages |
                             GatewayIntents.MessageContent 
        };

        _client = new DiscordSocketClient(config);

        _client.Log += Log;
        _client.MessageReceived += MessageReceivedAsync;

        await _client.LoginAsync(TokenType.Bot, TOKEN);
        await _client.StartAsync();

        await Task.Delay(-1); 
    }

    private Task Log(LogMessage msg)
    {
        Console.WriteLine(msg.ToString());
        return Task.CompletedTask;
    }

    private async Task MessageReceivedAsync(SocketMessage message)
    {
        if (message.Author.IsBot) return;

        if (message.Content.StartsWith("start"))
        {
            await message.Channel.SendMessageAsync("Please enter the account ID:");

            var userMessage = await WaitForNextMessageAsync(message.Channel, message.Author);

            if (userMessage == null)
            {
                await message.Channel.SendMessageAsync("No account ID received in time.");
                return;
            }

            string accountId = userMessage.Content.Trim();

            try
            {
                string result = await SendGetRequest(accountId);
                await message.Channel.SendMessageAsync(result);
            }
            catch (Exception ex)
            {
                await message.Channel.SendMessageAsync($"Error: {ex.Message}");
            }
        }
    }

    private async Task<SocketMessage> WaitForNextMessageAsync(ISocketMessageChannel channel, SocketUser author, int timeoutInSeconds = 30)
    {
        var tcs = new TaskCompletionSource<SocketMessage>();

        Task Func(SocketMessage msg)
        {
            if (msg.Author.Id == author.Id && msg.Channel.Id == channel.Id)
            {
                tcs.SetResult(msg);
            }
            return Task.CompletedTask;
        }

        _client.MessageReceived += Func;

        var delayTask = Task.Delay(timeoutInSeconds * 1000);
        var firstTask = await Task.WhenAny(tcs.Task, delayTask);

        _client.MessageReceived -= Func;

        if (firstTask == tcs.Task)
        {
            return await tcs.Task;
        }

        return null;
    }

    private static async Task<string> SendGetRequest(string accountId)
    {
        string url = $"https://api-info-app/player/{accountId}";
        using (HttpClient client = new HttpClient())
        {
            var response = await client.GetAsync(url);
            response.EnsureSuccessStatusCode();
            string jsonResult = await response.Content.ReadAsStringAsync();
            
          
            dynamic data = JsonConvert.DeserializeObject(jsonResult);

          
            return FormatResponse(data);
        }
    }

    private static string FormatResponse(dynamic data)
    {
        return $"**Basic Info:**\n" +
               $"- Account ID: {data.basicInfo.accountId}\n" +
               $"- Nickname: {data.basicInfo.nickname}\n" +
               $"- Level: {data.basicInfo.level}\n" +
               $"- Rank: {data.basicInfo.rank}\n" +
               $"- Region: {data.basicInfo.region}\n" +
               $"- Experience: {data.basicInfo.exp}\n\n" +
               $"**Clan Info:**\n" +
               $"- Clan Name: {data.clanBasicInfo.clanName}\n" +
               $"- Clan Level: {data.clanBasicInfo.clanLevel}\n" +
               $"- Members: {data.clanBasicInfo.memberNum}\n\n" +
               $"**Pet Info:**\n" +
               $"- Pet Name: {data.petInfo.name}\n" +
               $"- Pet Level: {data.petInfo.level}\n\n" +
               $"**Social Info:**\n" +
               $"- Signature: {data.socialInfo.signature}\n";
    }
}