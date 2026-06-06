namespace Helper;

public static class PathResolver
{
    public static string GetRootDirectory()
    {
        // 1. First, check if we are running locally on your Mac path
        string localMacPath = "/Users/raj/Dev/k3s";
        
        if (Directory.Exists(localMacPath))
        {
            return localMacPath;
        }

        // 2. Fallback: If you ever move this code to a pipeline, use the execution directory
        string baseDir = AppContext.BaseDirectory;
        return Path.GetFullPath(Path.Combine(baseDir, "..", "..", "..", ".."));
    }
}