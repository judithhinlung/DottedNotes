package org.codeperception.dottednotes;

public class Options {

  private String sourceFile;
  private String destinationFile;
  private boolean playScore = false;
  private boolean shouldPrintUsage = false;

  public Options(String[] args) {
    if ((args.length == 0) || (args[0].equals("--help") || args[0].equals("-h"))) {
      shouldPrintUsage = true;
    } else {
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

  boolean getShouldPrintUsage() {
    return shouldPrintUsage;
  }
}
