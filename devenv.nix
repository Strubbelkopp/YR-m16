{ pkgs, ... }:

{
  languages = {
    python = {
      enable = true;
      package = pkgs.python3.withPackages (ps: [
        ps.pytest
        ps.blessed
      ]);
    };
    rust = {
      enable = true;
    };
  };

  git-hooks.hooks = {
    pytest.enable = true;
  };
}