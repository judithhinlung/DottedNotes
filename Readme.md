# Dottednotes

DottedNotes converts music from MusicXML to MIDI. Conversion support for other formats, including braille music and Lilypond, is planned for future releases. Stay tuned!

## Building
```
mvn clean install
```

This command will (re)build the DottedNotes Maven artifacts (binary, source and doc).

## Usage

After building, the application is available in the target directory as dottednotes.jar.

To run the application:

```shell
cd target
java -jar dottednotes.jar <sourceFile> <options>
```

For example, to convert a file from MusicXML to MIDI and play the score:

```Shell
java -jar dottednotes.jar moonlight.xml --convert moonlight.midi --play
```

To get a list of all available commands and their usage, run the following command:

```shell
java -jar dottednotes.jar --help
```