package org.codeperception.dottednotes;

public class Options {

  private String sourceFile;
  private String destinationFile;
  private boolean playScore = false;

  public Options(String[] args) {
    for (int i = 0; i < args.length; i++) {
      String arg = args[i];
      if ((arg.equals("-p")) || (arg.equals("--play"))) {
        playScore = true;
      } else if ((arg.equals("-c")) || (arg.equals("--convert"))) {
        if (i < args.length - 1) {
          destinationFile = args[i + 1];
          i += 1;
        }
      } else if (i < args.length) {
        sourceFile = arg;
      } else {
        throw new IllegalArgumentException("Unknown option: " + arg);
      }
    }
  }

  String getSourceFile() {
    return sourceFile;
  }

  String getDestinationFile() {
    return destinationFile;
  }

  boolean getPlayScore() {
    return playScore;
  }
}
