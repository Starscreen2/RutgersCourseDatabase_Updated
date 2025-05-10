{pkgs}: {
  deps = [
    pkgs.openssh
    pkgs.glibcLocales
    pkgs.taskflow
    pkgs.rapidfuzz-cpp
    pkgs.imagemagick_light
    pkgs.postgresql
    pkgs.openssl
  ];
}
