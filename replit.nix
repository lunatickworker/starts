{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.libxcb
    pkgs.libxkbcommon
    pkgs.libxfixes
    pkgs.libxrandr
    pkgs.libxinerama
    pkgs.libxi
    pkgs.libxext
    pkgs.libx11
    pkgs.fontconfig
    pkgs.freetype
    pkgs.xorg.libxcb
    pkgs.dbus
    pkgs.atk
    pkgs.at-spi2-atk
    pkgs.cairo
    pkgs.cups
    pkgs.gdk-pixbuf
    pkgs.mesa
    pkgs.nss
    pkgs.pango
  ];
  env = {
    PYTHONUNBUFFERED = "1";
    PLAYWRIGHT_BROWSERS_PATH = "/tmp/.playwright";
  };
}
