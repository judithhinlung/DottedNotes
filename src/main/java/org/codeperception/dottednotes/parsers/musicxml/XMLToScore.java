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

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
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
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathExpressionException;
import javax.xml.xpath.XPathFactory;
import org.codeperception.dottednotes.math.Fraction;
import org.codeperception.dottednotes.music.*;
import org.w3c.dom.Document;
import org.w3c.dom.DocumentType;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;

/**
 * Class {@code XMLToScore}
 */
public class XMLToScore {

  //~ Instance fields
  public Score score;
  private static XPathFactory xPathFactory = XPathFactory.newInstance();
  private static DocumentBuilder documentBuilder;
  private Document document;
  private static final Logger LOG = Logger.getLogger(XMLToScore.class.getName());

  //~ Constructors
  /** Construct a XMLToScore object from an input stream
   *
   * @param inputStream  input stream containing the XML data
   * @param extension  extension of the given file
   */
  public XMLToScore(final InputStream inputStream, final String extension)
    throws ParserConfigurationException, IOException, SAXException, XPathExpressionException {
    setup();
    parse(inputStream, extension);
  }

  /** Construct a XMLToScore object from a  given URL
   *
   * @param filenameOrURL Local file path or absolute URL
   */
  public XMLToScore(final String filenameOrURL)
    throws ParserConfigurationException, IOException, SAXException, XPathExpressionException {
    setup();
    File file = new File(filenameOrURL);
    InputStream inputStream = null;
    String extension = null;
    int dot = filenameOrURL.lastIndexOf('.');
    if (dot != -1) {
      extension = filenameOrURL.substring(dot + 1);
    }
    if (file.exists()) {/* Local file */
      inputStream = new FileInputStream(file);
    } else {
      URL url = new URL(filenameOrURL);
      inputStream = url.openConnection().getInputStream();
    }
    parse(inputStream, extension);
  }

  //~ Methods
  /** Sets up the DOM parser
   */
  static void setup() {
    DocumentBuilderFactory documentBuilderFactory = DocumentBuilderFactory.newInstance();
    try {
      documentBuilder = documentBuilderFactory.newDocumentBuilder();
      documentBuilder.setEntityResolver(new MusicXMLEntityResolver());
    } catch (ParserConfigurationException e) {
      e.printStackTrace();
    }
  }

  /** Parses Music XML data from an input stream and constructs a music.Score object
   *
   * @param inputStream  input stream containing the XML data
   * @param extension  extension of the given file
   */
  private void parse(InputStream inputStream, String extension)
    throws ParserConfigurationException, IOException, SAXException, XPathExpressionException {
    HashMap<String, InputSource> Files = new HashMap<String, InputSource>();
    String zipEntryName = null;
    if ("mxl".equalsIgnoreCase(extension)) {
      ZipInputStream zipInputStream = new ZipInputStream(inputStream);
      ZipEntry zipEntry = null;

      while ((zipEntry = zipInputStream.getNextEntry()) != null) {
        InputSource currentInputSource = getInputSourceFromZipInputStream(zipInputStream);
        Files.put(zipEntry.getName(), currentInputSource);

        if ("META-INF/container.xml".equals(zipEntry.getName())) {
          Document container = documentBuilder.parse(currentInputSource);
          XPath xpath = xPathFactory.newXPath();
          zipEntryName =
            (String) xpath.evaluate(
              "container/rootfiles/rootfile/@full-path",
              container,
              XPathConstants.STRING
            );
        } else if (zipEntry.getName().equals(zipEntryName)) document =
          documentBuilder.parse(currentInputSource);
        zipInputStream.closeEntry();
      }
      if (document == null && !(zipEntryName == null)) {
        document = documentBuilder.parse(Files.get(zipEntryName));
      }
    } else {
      document = documentBuilder.parse(inputStream);
    }
    document.getDocumentElement().normalize();
    Element root = document.getDocumentElement();
    assert root.getTagName().equals("score-partwise");
    this.score = new Score();
    parseScore(this.score, root);
  }

  private InputSource getInputSourceFromZipInputStream(ZipInputStream zipInputStream)
    throws IOException {
    BufferedReader reader = new BufferedReader(new InputStreamReader(zipInputStream));
    StringBuilder stringBuilder = new StringBuilder();
    String string = null;
    while ((string = reader.readLine()) != null) stringBuilder.append(string + "\n");
    return new InputSource(new StringReader(stringBuilder.toString()));
  }

  public Score getScore() {
    return this.score;
  }

  public static void parseScore(Score score, Element element) {
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("identification")) {
          parseIdentification(score, child);
        } else if (tag.equals("work")) {
          parseWork(score, element);
        } else if (tag.equals("part-list")) {
          parseParts(score, child);
        } else if (tag.equals("part")) {
          String id = child.getAttribute("id");
          Part part = score.getPart(id);
          if (part != null) {
            parsePart(part, child);
          } else {
            System.err.println("No <score-part> for part with ID " + id);
          }
        }
      }
    }
  }

  private static void parseIdentification(Score score, Element element) {
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("creator")) {
          if (child.getAttribute("type").equals("composer")) {
            score.setComposer(child.getTextContent());
          } else if (child.getAttribute("type").equals("lyricist")) {
            score.setLyricist(child.getTextContent());
          }
        } else if (tag.equals("rights")) {
          String type = child.hasAttribute("type") ? child.getAttribute("type") : "";
          String rightsContent = child.getTextContent();
          String rights = String.format("%s: %s\n", type, rightsContent);
          score.addRights(rights);
        } else if (tag.equals("encoding")) {
          for (
            Node subnode = child.getFirstChild();
            subnode != null;
            subnode = subnode.getNextSibling()
          ) {
            if (subnode.getNodeType() == Node.ELEMENT_NODE) {
              Element encodingElement = (Element) node;
              String encodingTag = encodingElement.getTagName();
              if (encodingTag.equals("encoding-date")) {
                score.setEncodingDate(encodingElement.getTextContent());
              } else if (encodingElement.equals("encoder")) {
                score.setEncoder(encodingElement.getTextContent());
              } else if (encodingElement.equals("encoding-software")) {
                score.setEncodingSoftware(encodingElement.getTextContent());
              }
            }
          }
        }
      }
    }
  }

  private static void parseWork(Score score, Element element) {
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("work-number")) {
          score.setWorkNumber(child.getTextContent());
        } else if (tag.equals("work-title")) {
          score.setWorkTitle(child.getTextContent());
        } else if (tag.equals("opus")) {
          score.setOpus(child.getTextContent());
        } else if (tag.equals("movement-number")) {
          score.setMovementNumber(child.getTextContent());
        } else if (tag.equals("movement-title")) {
          score.setMovementTitle(child.getTextContent());
        }
      }
    }
  }

  static void parseParts(Score score, Element element) {
    ArrayList<Part> parts = score.getParts();
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("score-part")) {
          Part part = new Part(child.getAttribute("id"));
          score.addPart(part);
        }
      }
    }
  }

  /** Finds an element by id, starting from a given sourceElement
   *
   * @param sourceElement  the root element of the search
   * @param tagName  XML tag of the element
   * id  the ID of the element being searched for
   * @return  a Document.Element with the specified tagname and id
   */
  public static Element findElementById(
    Element sourceElement,
    String tagName,
    String id
  ) {
    NodeList tagList = sourceElement.getElementsByTagName(tagName);
    Element sinkElement = null;
    for (int i = 0; i < tagList.getLength(); i++) {
      Element currentElement = (Element) tagList.item(i);
      if (currentElement.getAttribute("id").equals(id)) {
        sinkElement = currentElement;
      }
    }
    return sinkElement;
  }

  static void parsePart(Part part, Element element) {
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("part-name")) {
          part.setName(child.getTextContent());
        } else if (tag.equals("part-abbreviation")) {
          part.setAbbreviation(child.getTextContent());
        } else if (tag.equals("score-instrument")) {
          parseScoreInstrument(part, child);
        } else if (tag.equals("midi-instrument")) {
          parseMidiInstrument(part, child);
        } else if (tag.equals("measure")) {
          parseMeasure(part, child);
        }
      }
    }
  }

  static void parseScoreInstrument(Part part, Element element) {
    String id = element.getAttribute("id");
    Instrument instrument = new Instrument(id);
    NodeList list = element.getChildNodes();
    for (int i = 0; i < list.getLength(); i++) {
      Node node = list.item(i);
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) (list.item(i));
        String tag = child.getTagName();
        if (tag.equals("instrument-name")) {
          instrument.setName(child.getTextContent());
        } else if (tag.equals("Instrument-sound")) {
          instrument.setInstrumentSound(child.getTextContent());
        }
      }
    }
    part.addInstrument(instrument);
  }

  /** Finds an Instrument from a given music.Part by ID
   *
   * @param id  ID of the instrument
   * part  a music.Part object
   */
  private static Instrument findInstrumentById(String id, Part part) {
    Instrument instrument = null;
    ArrayList<Instrument> instruments = part.getInstruments();
    for (int i = 0; i < instruments.size(); i++) {
      Instrument current = instruments.get(i);
      if (current.getId().equals(id)) {
        current = instrument;
      }
    }
    return instrument;
  }

  static void parseMidiInstrument(Part part, Element element) {
    String id = element.getAttribute("id");
    Instrument instrument = findInstrumentById(id, part);
    if (instrument == null) {
      instrument = new Instrument(id);
      part.addInstrument(instrument);
    }
    NodeList list = element.getChildNodes();
    for (int i = 0; i < list.getLength(); i++) {
      Node node = list.item(i);
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) (list.item(i));
        String tag = child.getTagName();
        if (tag.equals("midi-channel")) {
          int midiChannel = Integer.parseInt(child.getTextContent());
          instrument.setMidiChannel(midiChannel);
        } else if (tag.equals("midi-program")) {
          int midiProgram = Integer.parseInt(child.getTextContent());
          instrument.setMidiProgram(midiProgram);
        } else if (tag.equals("volume")) {
          int volume = Integer.parseInt(child.getTextContent());
          instrument.setVolume(volume);
        } else if (tag.equals("pan")) {
          int pan = Integer.parseInt(child.getTextContent());
          instrument.setPan(pan);
        } else if (tag.equals("elevation")) {
          int elevation = Integer.parseInt(child.getTextContent());
          instrument.setElevation(elevation);
        }
      }
    }
  }

  static void parseMeasure(Part part, Element element) {
    int number = Integer.parseInt(element.getAttribute("number"));
    Measure measure = new Measure(part, number);
    NodeList list = element.getChildNodes();
    for (int i = 0; i < list.getLength(); i++) {
      Node node = list.item(i);
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) (list.item(i));
        String tag = child.getTagName();
        if (tag.equals("note")) {
          Note note = parseNote(measure, child);
          measure.addElement(note);
        } else if (tag.equals("backup")) {
          parseBackup(measure, child);
        } else if (tag.equals("forward")) {
          parseForward(measure, child);
        } else if (tag.equals("attributes")) {
          parseAttributes(measure, child);
        } else if (tag.equals("direction")) {
          parseDirection(measure, child);
        } else if (tag.equals("figured-bass")) {
          FiguredBass figuredBass = parseFiguredBass(measure, child);
          measure.addElement(figuredBass);
        } else if (tag.equals("harmony")) {
          parseHarmony(measure, child);
        } else if (tag.equals("barline")) {
          parseBarline(measure, child);
        } else if (tag.equals("sound")) {
          parseSound(measure, child);
        }
      }
    }
    part.addMeasure(measure);
  }

  static Note parseNote(Measure measure, Element element) {
    Pitch pitch = null;
    Fraction duration = Fraction.ZERO;
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("pitch")) {
          pitch = parsePitch(child);
        } else if (tag.equals("unpitched")) {
          pitch = parseUnpitched(child);
        } else if (tag.equals("rest")) {
          pitch = parseRest(child);
        } else if (tag.equals("duration")) {
          duration = parseDuration(measure, child);
        }
      }
      if ((pitch != null) && (!duration.equals(Fraction.ZERO))) {
        break;
      }
    }
    if (pitch == null) {
      return null;
    }
    Note note = new Note(measure, pitch, duration);
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("grace")) {
          note.setGrace(parseGrace(child));
        } else if (tag.equals("chord")) {
          int staffNumber = Integer.parseInt(
            element.getElementsByTagName("staff").item(0).getTextContent()
          );
          int voiceNumber = Integer.parseInt(
            element.getElementsByTagName("voice").item(0).getTextContent()
          );
          Voice voice = measure.getStaff(staffNumber).getVoice(voiceNumber);
          ArrayList<MeasureElement> voiceElements = voice.getElements();
          MeasureElement prevMeasureElement = voiceElements.get(voiceElements.size() - 1);
          if (prevMeasureElement instanceof Chord) {
            Chord chord = (Chord) prevMeasureElement;
            chord.addNote(note);
          } else if (prevMeasureElement instanceof Note) {
            Note prevNote = (Note) prevMeasureElement;
            measure.removeElement(prevNote);
            Chord chord = new Chord(measure);
            chord.addNote(prevNote);
            chord.addNote(note);
            measure.addElement(chord);
          }
        } else if (tag.equals("time-modification")) {
          note.setTimeModification(parseTimeModification(child));
        } else if (tag.equals("instrument")) {
          note.setInstrumentId(parseInstrumentId(child));
        } else if (tag.equals("staff")) {
          int staffNumber = Integer.parseInt(child.getTextContent());
          note.setStaffNumber(staffNumber);
        } else if (tag.equals("voice")) {
          int voiceNumber = Integer.parseInt(child.getTextContent());
          note.setVoiceNumber(voiceNumber);
        } else if (tag.equals("type")) {
          note.setType(parseType(child));
        } else if (tag.equals("dot")) {
          note.setDotted(true);
        } else if (tag.equals("accidental")) {
          note.setAccidental(parseAccidental(child));
        } else if (tag.equals("notations")) {
          parseNotations(note, child);
        } else if (tag.equals("lyric")) {
          note.setLyric(parseLyric(child));
        }
      }
    }
    if (element.hasAttribute("pizzicato")) {
      note.setPizzicato(true);
    }
    return note;
  }

  private static int convertStep(String step) {
    return "CDEFGAB".indexOf(step.trim().toUpperCase());
  }

  private static Pitch parsePitch(Element element) throws MusicXMLParseException {
    int octave = 0;
    int alter = 0;
    int step = 0;
    NodeList list = element.getChildNodes();
    boolean foundOctave = false;
    boolean foundStep = false;
    for (int i = 0; i < list.getLength(); i++) {
      Node node = list.item(i);
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) (list.item(i));
        String tag = child.getTagName();
        if (tag.equals("alter")) {
          alter = Integer.parseInt(child.getTextContent());
        } else if (tag.equals("octave")) {
          octave = Integer.parseInt(child.getTextContent());
          foundOctave = true;
        } else if (tag.equals("step")) {
          step = convertStep(child.getTextContent());
          foundStep = true;
        }
      }
    }
    if (!foundOctave || !foundStep) {
      throw new MusicXMLParseException("Missing step or octave element");
    }
    return new Pitch("p", octave, step, alter);
  }

  private static Pitch parseUnpitched(Element element) {
    NodeList list = element.getChildNodes();
    int octave = -1;
    int step = 0;
    for (int i = 0; i < list.getLength(); i++) {
      Node node = list.item(i);
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) (list.item(i));
        String tag = child.getTagName();
        if (tag.equals("octave")) {
          octave = Integer.parseInt(child.getTextContent());
        } else if (tag.equals("step")) {
          step = convertStep(child.getTextContent());
        }
      }
    }
    return new Pitch("u", octave, step);
  }

  private static Pitch parseRest(Element element) {
    int displayOctave = 0;
    int displayStep = 0;
    boolean isMeasureRest = false;
    if (element.hasAttribute("measure")) {
      isMeasureRest = element.getAttribute("measure").equals("yes");
    }
    NodeList list = element.getChildNodes();
    for (int i = 0; i < list.getLength(); i++) {
      Node node = list.item(i);
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) (list.item(i));
        String tag = child.getTagName();
        if (tag.equals("octave")) {
          displayOctave = Integer.parseInt(child.getTextContent());
        } else if (tag.equals("step")) {
          displayStep = convertStep(child.getTextContent());
        }
      }
    }
    Pitch rest = new Pitch("r", displayOctave, displayStep);
    rest.setIsMeasureRest(isMeasureRest);
    return rest;
  }

  private static Grace parseGrace(Element element) {
    if (element.getAttributes().getLength() == 0) {
      return new Grace();
    }
    int stealTimePrevious = 0;
    int stealTimeFollowing = 0;
    int makeTime = 0;
    boolean slash = false;
    if (element.hasAttribute("steal-time-previous")) {
      stealTimePrevious = Integer.parseInt(element.getAttribute("steal-time-previous"));
    }
    if (element.hasAttribute("steal-time-following")) {
      stealTimeFollowing = Integer.parseInt(element.getAttribute("steal-time-following"));
    }
    if (element.hasAttribute("make-time")) {
      makeTime = Integer.parseInt(element.getAttribute("make-time"));
    }
    if (element.hasAttribute("slash")) {
      slash = element.getAttribute("slash").equals("yes");
    }
    return new Grace(stealTimePrevious, stealTimeFollowing, makeTime, slash);
  }

  private static Fraction parseDuration(Measure measure, Element element) {
    int numerator = Integer.parseInt(element.getTextContent());
    int denominator = measure.getDivisions();
    return new Fraction(numerator, denominator * 4).simplify();
  }

  private static TimeModification parseTimeModification(Element element) {
    int normalNotes = 0;
    int actualNotes = 0;
    String normalType = null;
    NodeList list = element.getChildNodes();
    for (int i = 0; i < list.getLength(); i++) {
      Node node = list.item(i);
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) (list.item(i));
        String tag = child.getTagName();
        if (tag.equals("normal-notes")) {
          normalNotes = Integer.parseInt(child.getTextContent());
        } else if (tag.equals("actual-notes")) {
          actualNotes = Integer.parseInt(child.getTextContent());
        } else if (tag.equals("normal-type")) {
          normalType = child.getTextContent();
        }
      }
    }
    TimeModification tm = null;
    if (normalType != null) {
      tm = new TimeModification(normalNotes, actualNotes, normalType);
    } else {
      tm = new TimeModification(normalNotes, actualNotes);
    }
    return tm;
  }

  private static String parseInstrumentId(Element element) {
    return element.getAttribute("id");
  }

  private static String parseType(Element element) {
    return element.getTextContent();
  }

  private static Accidental parseAccidental(Element element) {
    return new Accidental(element.getTextContent());
  }

  private static void parseNotations(Note note, Element element) {
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("tie")) {
          if (note.getTie() != null) {
            String type = child.getAttribute("type");
            Tie tie = new Tie(type);
            note.setTie(tie);
          }
        } else if (tag.equals("tied")) {
          if (note.getTie() != null) {
            String type = child.getAttribute("type");
            Tie tie = new Tie(type);
            note.setTie(tie);
          }
        } else if (tag.equals("slur")) {
          String type = child.getAttribute("type");
          if (note.getSlur() == null) {
            Slur slur = new Slur(type);
            note.setSlur(slur);
          } else {
            Slur slur = note.getSlur();
            slur.addType(type);
          }
        } else if (tag.equals("tuplet")) {
          note.setTuplet(parseTuplet(child));
        } else if (tag.equals("glissando")) {
          note.setGlissando(true);
        } else if (tag.equals("slide")) {
          note.setSlide(true);
        } else if (tag.equals("ornaments")) {
          parseOrnaments(note, child);
        } else if (tag.equals("articulations")) {
          parseArticulations(note, child);
        } else if (tag.equals("fermata")) {
          note.setFermata(true);
        } else if (tag.equals("dynamics")) {
          parseDynamic(note, child);
        } else if (tag.equals("arpeggiate")) {
          note.setArpeggiate(parseArpeggiate(child));
        }
      }
    }
  }

  private static Tuplet parseTuplet(Element element) {
    int normalNotes = 0;
    int actualNotes = 0;
    NodeList list = element.getChildNodes();
    for (int i = 0; i < list.getLength(); i++) {
      Node node = list.item(i);
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) (list.item(i));
        String tag = child.getTagName();
        if ((tag.equals("tuplet-normal")) && (child.hasAttribute("tuplet-number"))) {
          normalNotes = Integer.parseInt(child.getAttribute("tuplet-number"));
        } else if (
          (tag.equals("tuplet-actual")) && (child.hasAttribute("tuplet-number"))
        ) {
          actualNotes = Integer.parseInt(child.getAttribute("tuplet-number"));
        }
      }
    }
    return new Tuplet(normalNotes, actualNotes);
  }

  /** Converts a hyphenated string to camel case
   *
   * @param string  string to convert
   */
  private static String hyphenatedToCamel(String hyphenatedString) {
    String[] words = hyphenatedString.split("-");
    if (words.length < 2) {
      return words[0];
    }
    String camelString = words[0].toLowerCase();
    for (int i = 1; i < words.length; i++) {
      camelString.concat(words[i].toLowerCase());
    }
    return camelString;
  }

  private static void parseOrnaments(Note note, Element element) {
    ArrayList<Ornament> ornaments = note.getOrnaments();
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        String ornamentType = null;
        if (tag.equals("trill-mark")) {
          ornamentType = "trill";
        } else {
          ornamentType = hyphenatedToCamel(tag);
        }
        try {
          note.addOrnament(new Ornament(ornamentType));
        } catch (IllegalArgumentException e) {
          System.err.println("Unsupported ornament: " + ornamentType);
        }
      }
    }
  }

  private static void parseArticulations(Note note, Element element) {
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        String articulationType = hyphenatedToCamel(tag);
        try {
          note.addArticulation(new Articulation(articulationType));
        } catch (IllegalArgumentException e) {
          System.err.println("Unsupported articulation: " + articulationType);
        }
      }
    }
  }

  private static void parseTechnicals(Note note, Element element) {
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("harmonic")) {
          parseHarmonic(child);
        } else if (tag.equals("fingering")) {
          note.setFingering(parseFingering(child));
        } else if (tag.equals("pluck")) {
          note.setPluckFingering(parsePluck(child));
        } else if (tag.equals("fret")) {
          note.setFret(parseFret(child));
        } else if (tag.equals("string")) {
          note.setMusicString(parseMusicString(child));
        } else if (tag.equals("hole")) {
          note.setHole(parseHole(child));
        } else {
          String technicalType = hyphenatedToCamel(tag);
          try {
            note.addTechnical(new Technical(technicalType));
          } catch (IllegalArgumentException e) {
            System.err.println("Unsupported technical element: " + technicalType);
          }
        }
      }
    }
  }

  private static Harmonic parseHarmonic(Element element) {
    String type = null;
    NodeList list = element.getElementsByTagName("artificial");
    if (list.getLength() > 0) {
      type = "artificial";
    } else {
      type = "natural";
    }
    Harmonic harmonic = null;
    try {
      harmonic = new Harmonic(type);
    } catch (IllegalArgumentException e) {
      System.err.println("Invalid harmonic type: " + type);
    }
    return harmonic;
  }

  private static Fingering parseFingering(Element element) {
    int finger = Integer.parseInt(element.getTextContent());
    Fingering fingering = null;
    try {
      fingering = new Fingering(finger);
    } catch (IllegalArgumentException e) {
      System.err.println("Unknown fingering: " + finger);
    }
    return fingering;
  }

  private static PluckFingering parsePluck(Element element) {
    String finger = element.getTextContent();
    PluckFingering pluckFingering = null;
    try {
      pluckFingering = new PluckFingering(finger);
    } catch (IllegalArgumentException e) {
      System.err.println("Invalid pluck fingering: " + finger);
    }
    return pluckFingering;
  }

  private static Fret parseFret(Element element) {
    return new Fret(Integer.parseInt(element.getTextContent()));
  }

  public static MusicString parseMusicString(Element element) {
    return new MusicString(Integer.parseInt(element.getTextContent()));
  }

  private static Hole parseHole(Element element) {
    Hole hole = null;
    Element holeClosed = (Element) (element.getElementsByTagName("hole-closed").item(0));
    String type = holeClosed.getTextContent();
    try {
      hole = new Hole(type);
    } catch (IllegalArgumentException e) {
      System.err.println("Invalid hole symbol: " + type);
    }
    return hole;
  }

  private static void parseDynamic(Note note, Element element) {
    NodeList list = element.getChildNodes();
    for (int i = 0; i < list.getLength(); i++) {
      Element child = (Element) (list.item(i));
      String type = child.getTagName();
      try {
        note.setDynamic(new Dynamic(type));
      } catch (IllegalArgumentException e) {
        System.err.println("Unknown dynamic: " + type);
      }
    }
  }

  private static Arpeggiate parseArpeggiate(Element element) {
    if (element.hasAttribute("number") && element.hasAttribute("direction")) {
      int num = Integer.parseInt(element.getAttribute("number"));
      String dir = element.getAttribute("direction");
      return new Arpeggiate(num, dir);
    }
    return new Arpeggiate();
  }

  private static Lyric parseLyric(Element element) {
    String text = null;
    String syllabic = null;
    boolean hasElision = false;
    boolean isExtended = false;
    NodeList list = element.getChildNodes();
    for (int i = 0; i < list.getLength(); i++) {
      Element child = (Element) list.item(i);
      String tag = child.getTagName();
      if (tag.equals("text")) {
        text = child.getTextContent();
      } else if (tag.equals("syllabic")) {
        syllabic = child.getTextContent();
      } else if (tag.equals("extended")) {
        isExtended = true;
      } else if (tag.equals("elision")) {
        hasElision = true;
      }
    }
    if ((text != null && syllabic != null) && (isExtended && hasElision)) {
      try {
        return new Lyric(text, syllabic, hasElision, isExtended);
      } catch (IllegalArgumentException e) {
        System.err.println(
          "Invalid lyric arguments: " +
          text +
          ", " +
          syllabic +
          ", " +
          hasElision +
          ", " +
          isExtended
        );
      }
    } else if (text != null && syllabic != null) {
      try {
        return new Lyric(text, syllabic);
      } catch (IllegalArgumentException e) {
        System.err.println("Invalid lyric arguments: " + text + ", " + syllabic);
      }
    } else if (text != null) {
      try {
        return new Lyric(text);
      } catch (IllegalArgumentException e) {
        System.err.println("Invalid lyric arguments: " + text);
      }
    }
    return null;
  }

  static FiguredBass parseFiguredBass(Measure measure, Element element) {
    Fraction duration = Fraction.ZERO;
    String prefix = null;
    int number = 0;
    String suffix = null;
    FiguredBass figuredBass = null;
    if (element.hasAttribute("duration")) {
      int numerator = Integer.parseInt(element.getAttribute("duration"));
      int denominator = measure.getDivisions();
      duration = new Fraction(numerator, (denominator * 4)).simplify();
    }
    Element figureElement = (Element) element.getElementsByTagName("figure").item(0);
    NodeList list = figureElement.getChildNodes();
    for (int i = 0; i < list.getLength(); i++) {
      Element child = (Element) list.item(i);
      String tag = child.getTagName();
      if (tag.equals("prefix")) {
        prefix = child.getTextContent();
      } else if (tag.equals("number")) {
        number = Integer.parseInt(child.getTextContent());
      } else if (tag.equals("suffix")) {
        suffix = child.getTextContent();
      }
    }
    if (prefix != null && number > 0 && suffix != null) {
      try {
        figuredBass = new FiguredBass(measure, prefix, number, suffix);
      } catch (IllegalArgumentException e) {
        System.err.println(
          "Invalid Figured Bass arguments: " + prefix + ", " + number + ", " + suffix
        );
      }
    } else if (number > 0) {
      try {
        figuredBass = new FiguredBass(measure, number);
      } catch (IllegalArgumentException e) {
        System.err.println("Invalid Figured Bass number argument: " + number);
      }
      if (prefix != null) {
        try {
          figuredBass.addPrefix(prefix);
        } catch (IllegalArgumentException e) {
          System.err.println("Invalid Figured bass prefix argument: " + prefix);
        }
      }
      if (suffix != null) {
        try {
          figuredBass.addSuffix(suffix);
        } catch (IllegalArgumentException e) {
          System.err.println("Invalid Figured bass argument: " + suffix);
        }
      }
    }
    return figuredBass;
  }

  static void parseBackup(Measure measure, Element element) {
    Fraction duration = Fraction.ZERO;
    NodeList list = element.getElementsByTagName("duration");
    if (list.getLength() == 1) {
      Element durationElement = (Element) element
        .getElementsByTagName("duration")
        .item(0);
      duration = parseDuration(measure, durationElement);
    }
    measure.addElement(new Backup(measure, duration));
  }

  static void parseForward(Measure measure, Element element) {
    int numerator = 0;
    int denominator = measure.getDivisions();
    Fraction duration = Fraction.ZERO;
    int staffNumber = 0;
    int voiceNumber = 0;
    NodeList list = element.getElementsByTagName("duration");
    if (list.getLength() == 1) {
      Element durationElement = (Element) element
        .getElementsByTagName("duration")
        .item(0);
      duration = parseDuration(measure, durationElement);
    }
    list = element.getElementsByTagName("staff");
    if (list.getLength() == 1) {
      staffNumber = Integer.parseInt(list.item(0).getTextContent());
    }
    list = element.getElementsByTagName("voice");
    if (list.getLength() == 1) {
      voiceNumber = Integer.parseInt(list.item(0).getTextContent());
    }
    Forward forward = new Forward(measure, duration);
    forward.setStaffNumber(staffNumber);
    forward.setVoiceNumber(voiceNumber);
    measure.addElement(forward);
  }

  static void parseAttributes(Measure measure, Element element) {
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("divisions")) {
          int divisions = Integer.parseInt(child.getTextContent());
          measure.setDivisions(divisions);
        } else if (tag.equals("key")) {
          parseKey(measure, child);
        } else if (tag.equals("time")) {
          parseTime(measure, child);
        } else if (tag.equals("staves")) {
          int staves = Integer.parseInt(child.getTextContent());
          measure.getPart().setStaves(staves);
          measure.createStaves();
        } else if (tag.equals("clef")) {
          parseClef(measure, child);
        } else if (tag.equals("transpose")) {
          parseTranspose(measure, child);
        }
      }
    }
  }

  private static void parseKey(Measure measure, Element element) {
    Element fifths = (Element) element.getElementsByTagName("fifths").item(0);
    int type = Integer.parseInt(fifths.getTextContent());
    KeySignature key = new KeySignature(type);
    measure.setKey(key);
  }

  public static void parseTime(Measure measure, Element element) {
    Element beatsElement = (Element) element.getElementsByTagName("beats").item(0);
    Element beatTypeElement = (Element) element.getElementsByTagName("beat-type").item(0);
    int numerator = Integer.parseInt(beatsElement.getTextContent());
    int denominator = Integer.parseInt(beatTypeElement.getTextContent());
    TimeSignature time = new TimeSignature(numerator, denominator);
    measure.setTime(time);
  }

  private static void parseClef(Measure measure, Element element) {
    String sign = null;
    int line = 0;
    int octaveChange = 0;
    int staffNumber = 0;
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("sign")) {
          sign = child.getTextContent();
        } else if (tag.equals("line")) {
          line = Integer.parseInt(child.getTextContent());
        } else if (tag.equals("clef-octave-change")) {
          octaveChange = Integer.parseInt(child.getTextContent());
        }
      }
    }
    Clef clef = new Clef(sign, line);
    if (octaveChange != 0) {
      clef.setOctaveChange(octaveChange);
    }
    if (element.hasAttribute("staff-number")) {
      clef.setStaffNumber(Integer.parseInt(element.getAttribute("number")));
    }
    Part part = measure.getPart();
    part.addClef(clef);
  }

  static void parseTranspose(Measure measure, Element element)
    throws MusicXMLParseException {
    if (element.getElementsByTagName("chromatic").getLength() == 0) {
      throw new MusicXMLParseException("Missingchromatic step in transpose element");
    }
    int step = Integer.parseInt(
      element.getElementsByTagName("chromatic").item(0).getTextContent()
    );
    Transpose transpose = new Transpose(step);
    if (element.hasAttribute("number")) {
      transpose.setStaffNumber(Integer.parseInt(element.getAttribute("number")));
    }
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("diatonic")) {
          int diatonicPitch = Integer.parseInt(child.getTextContent());
          transpose.setDiatonicPitch(diatonicPitch);
        } else if (tag.equals("octave-change")) {
          int octaveChange = Integer.parseInt(child.getTextContent());
          transpose.setOctaveChange(octaveChange);
        } else if (tag.equals("doubling")) {
          String doubling = child.getTextContent();
          if (doubling.equals("yes")) {
            transpose.setDoubling(true);
          }
        }
      }
    }
  }

  static void parseDirection(Measure measure, Element element) {
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("words")) {
          String text = child.getTextContent();
          measure.addElement(new TextDirection(measure, text));
        } else if (tag.equals("pedal")) {
          parsePedal(measure, child);
        } else if (tag.equals("metronome")) {
          parseMetronome(measure, child);
        } else if (tag.equals("sound")) {
          parseSound(measure, child);
        }
      }
    }
  }

  private static void parsePedal(Measure measure, Element element)
    throws MusicXMLParseException {
    NodeList list = element.getElementsByTagName("type");
    if (list.getLength() == 0) {
      throw new MusicXMLParseException("Missing type element for pedal");
    }
    String type = list.item(0).getTextContent();
    Pedal pedal = new Pedal(measure, type);
    measure.addElement(pedal);
  }

  private static int getTimeOnly(Element element) {
    int time = 0;
    if (element.hasAttribute("time-only")) {
      time += Integer.parseInt(element.getAttribute("time-only"));
    }
    return time;
  }

  private static void parseMetronome(Measure measure, Element element)
    throws MusicXMLParseException {
    String beatUnit = null;
    int perMinute = 0;
    Note metronomeNote = null;
    String metronomeRelation = null;
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("beat-unit")) {
          beatUnit = child.getTextContent();
        } else if (tag.equals("per-minute")) {
          String perMinuteText = child.getTextContent();
          perMinute = Integer.parseInt(perMinuteText.replaceAll("\\D+", ""));
        } else if (tag.equals("metronome-note")) {
          Note note = parseNote(measure, child);
          measure.addElement(note);
        } else if (tag.equals("metronome-relation")) {
          metronomeRelation = child.getTextContent();
        }
      }
    }
    if ((beatUnit == null) || (perMinute == 0)) {
      throw new MusicXMLParseException(
        "Missing the 'beat-unit' or 'per-minute' elements for the 'metronome' element"
      );
    }
    Metronome metronome = new Metronome(measure, beatUnit, perMinute);
    if (metronomeNote != null) {
      metronome.setMetronomeNote(metronomeNote);
    }
    if (metronomeRelation != null) {
      metronome.setMetronomeRelation(metronomeRelation);
    }
    measure.addElement(metronome);
  }

  private static void parseSound(Measure measure, Element element) {
    Sound sound = new Sound(measure);
    if (element.hasAttribute("tempo")) {
      int tempo = Integer.parseInt(element.getAttribute("tempo"));
      sound.setTempo(tempo);
    } else if (element.hasAttribute("dynamics")) {
      int velocity = Integer.parseInt(element.getAttribute("dynamics"));
      sound.setVelocity(velocity);
    } else if (element.hasAttribute("dacapo")) {
      sound.setDacapo(true);
    } else if (element.hasAttribute("segno")) {
      sound.setSegno(true);
    } else if (element.hasAttribute("coda")) {
      sound.setCoda(true);
    } else if (element.hasAttribute("dalsegno")) {
      sound.setDalsegno(true);
    } else if (element.hasAttribute("tocoda")) {
      sound.setTocoda(true);
    } else if (element.hasAttribute("forward-repeat")) {
      sound.setForwardRepeat(true);
    } else if (element.hasAttribute("fine")) {
      sound.setFine(true);
    } else if (element.hasAttribute("pizzicato")) {
      sound.setPizzicato(true);
    }
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("midi-instrument")) {
          Part part = measure.getPart();
          parseMidiInstrument(part, child);
          String id = child.getAttribute("id");
          sound.setInstrument(part.getInstrument(id));
        } else if (tag.equals("offset")) {
          int numerator = Integer.parseInt(child.getTextContent());
          int denominator = measure.getDivisions();
          Fraction offset = new Fraction(numerator, denominator);
          sound.setOffset(offset);
        }
      }
    }
    measure.addElement(sound);
  }

  static void parseHarmony(Measure measure, Element element) {
    Harmony.Root root;
    String kind;
    int inversion;
    Harmony.Bass bass;
    Harmony.Degree degree;
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("root") || tag.equals("function")) {
          root = parseRoot(child);
        } else if (tag.equals("kind")) {
          kind = child.getTextContent();
        } else if (tag.equals("inversion")) {
          inversion = Integer.parseInt(child.getTextContent());
        } else if (tag.equals("bass")) {
          bass = parseBass(child);
        } else if (tag.equals("degree")) {
          degree = parseDegree(child);
        }
      }
    }
  }

  private static Harmony.Root parseRoot(Element element) {
    Harmony.Root root = null;
    int step = 0;
    int alter = 0;
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("root-step")) {
          step = convertStep(child.getTextContent());
        } else if (tag.equals("root-alter")) {
          alter = Integer.parseInt(child.getTextContent());
        }
      }
    }
    root = new Harmony.Root(step, alter);
    return root;
  }

  private static Harmony.Bass parseBass(Element element) {
    int step = 0;
    int alter = 0;
    Harmony.Bass bass;
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("bass-step")) {
          step = convertStep(child.getTextContent());
        } else if (tag.equals("bass-alter")) {
          alter = Integer.parseInt(child.getTextContent());
        }
      }
    }
    bass = new Harmony.Bass(step, alter);
    return bass;
  }

  private static Harmony.Degree parseDegree(Element element) {
    int value = 0;
    int alter = 0;
    String type = null;
    Harmony.Degree degree;
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("degree-value")) {
          value = Integer.parseInt(child.getTextContent());
        } else if (tag.equals("degree-alter")) {
          alter = Integer.parseInt(child.getTextContent());
        } else if (tag.equals("degree-type")) {
          type = child.getTextContent();
        }
      }
    }
    if (value == 0) {
      return null;
    }
    degree = new Harmony.Degree(value);
    degree.setAlter(alter);
    degree.setType(type);
    return degree;
  }

  public static void parseBarline(Measure measure, Element element) {
    Barline barline = new Barline(measure);
    if (element.hasAttribute("location")) {
      barline.setLocation(element.getAttribute("location"));
    } else if (element.hasAttribute("segno")) {
      barline.setSegno(true);
    } else if (element.hasAttribute("coda")) {
      barline.setCoda(true);
    }
    for (
      Node node = element.getFirstChild();
      node != null;
      node = node.getNextSibling()
    ) {
      if (node.getNodeType() == Node.ELEMENT_NODE) {
        Element child = (Element) node;
        String tag = child.getTagName();
        if (tag.equals("ending")) {
          barline.setEnding(parseEnding(element));
        } else if (tag.equals("repeat")) {
          barline.setRepeat(parseRepeat(child));
        }
      }
    }
  }

  private static Ending parseEnding(Element element) throws MusicXMLParseException {
    int number = element.hasAttribute("number")
      ? Integer.parseInt(element.getAttribute("number"))
      : 0;
    String type = element.hasAttribute("type") ? element.getAttribute("type") : null;
    if (number == 0) {
      throw new MusicXMLParseException("Ending missing required `number` attribute");
    }
    if (type == null) {
      throw new MusicXMLParseException("Ending missing required `type` attribute");
    }
    Ending ending = new Ending(number, type);
    return ending;
  }

  private static Repeat parseRepeat(Element element) {
    if (!element.hasAttribute("direction")) {
      return null;
    }
    String direction = element.getAttribute("direction");
    Repeat repeat = new Repeat(direction);
    if (element.hasAttribute("times")) {
      int times = Integer.parseInt(element.getAttribute("times"));
      repeat.setTimes(times);
    }
    return repeat;
  }
}
