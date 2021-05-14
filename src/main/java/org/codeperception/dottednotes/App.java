/**
 * DottedNotes: -- Braille Music Conversion Utility
 *
 * Copyright 2021 Judith Lung  All Rights Reserved.
 *
 * This code is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License version 3, as
 * published by the Free Software Foundation.
 *
 * This code is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this work; if not, see <http://www.gnu.org/licenses/>.
 */

package org.codeperception.dottednotes;

import java.io.*;
import javax.sound.midi.*;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.xpath.XPathExpressionException;
import org.codeperception.dottednotes.converters.midi.*;
import org.codeperception.dottednotes.music.*;
import org.codeperception.dottednotes.parsers.musicxml.*;
import org.xml.sax.SAXException;

public class App {

  public static void main(String[] args)
    throws FileNotFoundException, InvalidMidiDataException {
    Score score = null;
    Options options = new Options(args);
    if (options.getShouldPrintUsage()) {
      printUsage();
      return;
    }
    if (options.getSourceFile() != null) {
      score = getScore(options.getSourceFile());
    }
    ScoreToMidi midiScore = null;
    boolean playScore = options.getPlayScore();
    boolean exportToMidi = (options.getDestinationFile() != null);
    if ((score != null) && (playScore || exportToMidi)) {
      midiScore = new ScoreToMidi(score);
      if (playScore) {
        try {
          MidiPlayer player = new MidiPlayer();
          player.play(midiScore.getSequence());
        } catch (MidiUnavailableException e) {
          System.err.println("MIDI playback unavailable.");
          e.printStackTrace();
        } catch (InvalidMidiDataException e) {
          e.printStackTrace();
        }
      }
      if (exportToMidi) {
        try {
          FileOutputStream fis = new FileOutputStream(options.getDestinationFile());
          MidiSystem.write(midiScore.getSequence(), 1, fis);
          fis.close();
        } catch (IOException e) {
          e.printStackTrace();
        }
      }
    }
  }

  static Score getScore(String fileName) {
    Score score = null;
    File file = new File(fileName);
    if (!file.exists()) {
      System.err.println("File " + fileName + " not found.");
      System.exit(1);
    }
    String ext = getExtension(fileName);
    if ((ext.equals("xml")) || (ext.equals("mxl"))) {
      try {
        score = new XMLToScore(fileName).getScore();
      } catch (IOException e) {
        e.printStackTrace();
      } catch (SAXException e) {
        e.printStackTrace();
      } catch (ParserConfigurationException e) {
        e.printStackTrace();
      } catch (XPathExpressionException e) {
        e.printStackTrace();
      }
    }
    return score;
  }

  static String getExtension(String fileName) {
    int dotPosition = 0;
    for (int i = 0; i < fileName.length(); i++) {
      if (fileName.charAt(i) == '.') {
        dotPosition = i;
      }
    }
    return fileName.substring(dotPosition + 1);
  }

  static void printUsage() {
    String usage =
      "java -jar dottednotes.1.0.0.jar --help\n" +
      "  Outputs the usage instructions for all commands\n" +
      "  aliases: -h\n" +
      "java -jar dottednotes.1.0.0.jar <file|URL> <options...>\n" +
      "  Imports a file for conversion.\n" +
      "  A path is expected, relative to the root of the project.\n" +
      "  --play Plays the complete score.\n" +
      "  alias: -p\n" +
      "  --convert <file> Exports the score in the format specified by the file extension.\n." +
      "  A path is expected, relative to the root of the project.\n" +
      "  alias: -c\n";
    System.out.println(usage);
    System.exit(1);
  }
}
