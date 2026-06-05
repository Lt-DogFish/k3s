using Factories;
using CustomInterfaces;

Console.WriteLine("Starting Local C# GitOps Generation Engine...");

var factories = new List<IAppFactory>
{
    new PortfolioFactory(),
    new MinioFactory()
};

foreach (var factory in factories)
{
    factory.Generate();
}

Console.WriteLine("Manifests Generated");