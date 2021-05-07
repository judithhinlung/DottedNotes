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

package org.codeperception.dottednotes.parsers.musicxml;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.StringReader;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.logging.Logger;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import javax.sound.midi.*;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathExpressionException;
import javax.xml.xpath.XPathFactory;
import junit.framework.TestCase;
import org.codeperception.dottednotes.converters.midi.*;
import org.codeperception.dottednotes.math.Fraction;
import org.codeperception.dottednotes.music.*;
import org.junit.Test;
import org.w3c.dom.Document;
import org.w3c.dom.Document;
import org.w3c.dom.DocumentType;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;

public class XMLToScoreTest extends TestCase {

  //-----------------//
  // checkBasicParsing //
  //-----------------//
  public void testBasicParsing()
    throws SAXException, ParserConfigurationException, IOException, XPathExpressionException {
    String file = "src/test/resources/c-scale.xml";
    XMLToScore parser = new XMLToScore(file);
    Score score = parser.getScore();
    assertEquals(24, score.getDivisions());
    assertEquals(1, score.getParts().size());
    Part part = score.getPart("P1");
    assertEquals(2, part.getMeasures().size());
    Measure m1 = part.getMeasure(1);
    assertEquals(new Fraction(4, 4), m1.getTime());
    Voice v1 = m1.getStaff(1).getVoice(1);
    assertEquals(v1.getElements().size(), 4);
    Note note1 = (Note) v1.getElements().get(0);
    assertEquals(0, note1.getPitch().getStep());
    assertEquals(4, note1.getPitch().getOctave());
    assertEquals(new Fraction(1, 4), note1.getDuration());
    Note note2 = (Note) v1.getElements().get(1);
    assertEquals(1, note2.getPitch().getStep());
    assertEquals(4, note2.getPitch().getOctave());
    assertEquals(new Fraction(1, 4), note2.getDuration());
    Note note3 = (Note) v1.getElements().get(2);
    assertEquals(2, note3.getPitch().getStep());
    assertEquals(4, note3.getPitch().getOctave());
    assertEquals(new Fraction(1, 4), note3.getDuration());
    Note note4 = (Note) v1.getElements().get(3);
    assertEquals(3, note4.getPitch().getStep());
    assertEquals(4, note4.getPitch().getOctave());
    assertEquals(new Fraction(1, 4), note4.getDuration());
  }

  public void testBasicPlayback()
    throws SAXException, ParserConfigurationException, IOException, XPathExpressionException, InvalidMidiDataException, MidiUnavailableException {
    String file = "src/test/resources/c-scale.xml";
    XMLToScore parser = new XMLToScore(file);
    Score score = parser.getScore();
    ScoreToMidi midiScore = new ScoreToMidi(score);
    MidiPlayer player = new MidiPlayer();
    Sequence sequence = midiScore.getSequence();
    // player.play(sequence);
  }
}
