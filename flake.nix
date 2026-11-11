{
  description = "InvenTree IPN generator plugin, packaged for inventree-flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    inventree.url = "github:mpashton/inventree-flake";
    inventree.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, inventree }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAll = f: nixpkgs.lib.genAttrs systems (s: f s nixpkgs.legacyPackages.${s});
      project = (builtins.fromTOML (builtins.readFile ./pyproject.toml)).project;
    in {
      packages = forAll (system: pkgs: {
        default = self.packages.${system}.inventree-ipn-generator;
        inventree-ipn-generator = inventree.lib.inventreePlugin pkgs {
          pname = "inventree-ipn-generator";
          inherit (project) version;
          src = self;
          module = "ipn_generator";
          slug = "ipngen";
          pluginConfigs.ENABLE_PLUGINS_EVENTS = true;
          meta = { description = project.description; homepage = project.urls.Homepage; license = nixpkgs.lib.licenses.mit; };
        };
      });
    };
}
