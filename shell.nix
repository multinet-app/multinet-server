with import <nixpkgs> {};

let manyLinuxFile = writeTextDir "_manylinux.py"
  ''
  print("in _manylinux.py")
  manylinux1_compatible = True
  '';
in
(buildFHSUserEnv {
  name = "multinet-python-env";
  targetPkgs = pkgs: with pkgs; [
    python3
    pipenv
    ncurses.dev
  ];

  profile = ''
    export PYTHONPATH=${manyLinuxFile.out}:/usr/lib/python3.6/site-packages
    export SOURCE_DATE_EPOCH=$(date +%s)
  '';
  runScript = "zsh";
}).env
