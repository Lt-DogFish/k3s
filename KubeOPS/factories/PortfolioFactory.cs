using k8s.Models;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

using CustomInterfaces;
using Helper;
namespace Factories;

public class PortfolioFactory : IAppFactory
{

    private readonly string _targetDir = Path.Combine(PathResolver.GetRootDirectory(), "KubeOPS", "dev", "portfolio");


    public void Generate()
    {
        Directory.CreateDirectory(_targetDir);

        var deployment = new V1Deployment
        {
            ApiVersion = "apps/v1",
            Kind = "Deployment",
            Metadata = new V1ObjectMeta { Name = "portfolio-site", NamespaceProperty = "esp32" },
            Spec = new V1DeploymentSpec
            {
                Replicas = 1,
                Selector = new V1LabelSelector { MatchLabels = new Dictionary<string, string> { { "app", "portfolio" } } },
                Template = new V1PodTemplateSpec
                {
                    Metadata = new V1ObjectMeta { Labels = new Dictionary<string, string> { { "app", "portfolio" } } },
                    Spec = new V1PodSpec
                    {
                        Containers = new List<V1Container>
                        {
                            new V1Container
                            {
                                Name = "web",
                                Image = "ghcr.io/lt-dogfish/portfolio-site:latest",
                                ImagePullPolicy = "Always"
                            }
                        }
                    }
                }
            }
        };

        WriteYaml(deployment, "deployment.yaml");
        Console.WriteLine("  └─ Generated Portfolio manifests successfully.");
    }

    private void WriteYaml(object obj, string filename)
    {
        // YamlDotNet converts Kubernetes model properties to lowercase camelCase text strings
        var serializer = new SerializerBuilder()
            .WithNamingConvention(CamelCaseNamingConvention.Instance)
            .ConfigureDefaultValuesHandling(DefaultValuesHandling.OmitNull)
            .Build();

        var yaml = serializer.Serialize(obj);
        File.WriteAllText(Path.Combine(_targetDir, filename), yaml);
        Console.WriteLine($"Manifest created at: {Path.Combine(_targetDir, filename)}");
        Console.WriteLine("Done");
    }
}