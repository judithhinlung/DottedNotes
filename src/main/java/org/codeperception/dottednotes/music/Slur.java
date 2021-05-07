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

package org.codeperception.dottednotes.music;

import java.util.ArrayList;

public class Slur {

  ArrayList<String> types;

  public Slur(String type) {
    this.types = new ArrayList<String>();
    String[] availableTypes = new String[] { "start", "stop", "continue" };
    if (!Utils.contains(type, availableTypes)) {
      throw new IllegalArgumentException("Invalid slur type: " + type);
    }
    this.types.add(type);
  }

  public ArrayList<String> getTypes() {
    return this.types;
  }

  public void addType(String type) {
    this.types.add(type);
  }
}
