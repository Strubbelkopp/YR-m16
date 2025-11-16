{
  description = "Dev environment for Python";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { nixpkgs, flake-utils, ... }: let
      pythonVersion = "3.13";
    in flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {
        inherit system;
      };

      concatMajorMinor = v: pkgs.lib.pipe v [
        pkgs.lib.versions.splitVersion
        (pkgs.lib.sublist 0 2)
        pkgs.lib.concatStrings
      ];
      python = pkgs."python${concatMajorMinor pythonVersion}";
    in {
      devShells.default = pkgs.mkShellNoCC {
        venvDir = ".venv";

        postShellHook = ''
          venvVersionWarn() {
            local venvVersion
            venvVersion="$("$venvDir/bin/python" -c 'import platform; print(platform.python_version())')"

            [[ "$venvVersion" == "${python.version}" ]] && return

            cat <<EOF
          Warning: Python version mismatch: [$venvVersion (venv)] != [${python.version}]
                    Delete '$venvDir' and reload to rebuild for version ${python.version}
          EOF
          }

          venvVersionWarn
        '';

        packages = with python.pkgs; [
          venvShellHook
          pip

          pytest
          unicurses
        ];
      };
    }
  );
}