{
  description = "A Discord bot that watches RSS feeds";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
  };

  outputs = { self, nixpkgs, ... }:
    let
      forAllSystems = gen:
        nixpkgs.lib.genAttrs nixpkgs.lib.systems.flakeExposed
        (system: gen nixpkgs.legacyPackages.${system});
    in {
      packages = forAllSystems (pkgs: {
        scrape = pkgs.callPackage ./scrape {};
        stats = pkgs.callPackage ./stats {};
      });

      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          # # buildInputs = [
          # #   # inherit (self.packages.${pkgs.system}) scrape stats
          # #   self.packages.${pkgs.system}.scrape
          # # ];
          # buildInputs = builtins.attrValues {
          #   inherit (self.packages.${pkgs.system}) scrape stats;
          # };
          buildInputs = builtins.attrValues self.packages.${pkgs.system};
        };
      });
    };
}
