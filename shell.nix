with import <nixpkgs> {};

stdenv.mkDerivation {
  name = "multinet-python-env";
  src = null;

  buildInputs = [
    python37Full
    python37Packages.virtualenv
    python37Packages.pip

    ncurses.dev
  ];

  shellHook = ''
    SOURCE_DATE_EPOCH=$(date +%s)
  '';
}
