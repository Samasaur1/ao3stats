{ lib, writers, python3Packages }:

(writers.writePython3Bin "scrape" {
  libraries = with python3Packages; [
    tqdm
    requests
    beautifulsoup4
  ];
  flakeIgnore = [ "E501" "F541" "E302" "E305" "E722" "F823" ];
  # flakeIgnore = [ "E261" "E262" "E302" "E501" "E722" "F541" "W292" ];
} (builtins.readFile ./main.py)) // {
  meta = with lib; {
    # description = "A Discord bot that watches RSS feeds";
    # homepage = "https://github.com/Samasaur1/rssbot";
  };
}
