{ lib, writers, python3Packages }:

(writers.writePython3Bin "scrape" {
  libraries = with python3Packages; [
    tqdm
    requests
    beautifulsoup4
  ];
  flakeIgnore = [ "E501" "F541" "E302" "E305" "E722" "F823" ];
} (builtins.readFile ./main.py)) // {
  meta = with lib; {
    description = "Scrape your AO3 history page to a JSON file";
    homepage = "https://github.com/Samasaur1/ao3stats";
    mainProgram = "scrape";
  };
}
