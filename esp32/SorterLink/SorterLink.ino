#include <Arduino.h>
#include <string.h>

// USB link for the first bench test. Each command ends with a newline.
char command[48];
size_t length = 0;
bool overflow = false;

void reply(const char *line) {
  if (strcmp(line, "PING") == 0) {
    Serial.println("PONG");
  } else if (strcmp(line, "STATUS") == 0) {
    Serial.println("READY LINK_TEST");
  } else if (strcmp(line, "TEST PCB") == 0) {
    Serial.println("TEST_OK PCB");
  } else if (strcmp(line, "TEST BATTERY") == 0) {
    Serial.println("TEST_OK BATTERY");
  } else if (strcmp(line, "TEST DISPLAY") == 0) {
    Serial.println("TEST_OK DISPLAY");
  } else {
    Serial.println("ERR UNKNOWN_COMMAND");
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("READY LINK_TEST");
}

void loop() {
  while (Serial.available() > 0) {
    const char ch = static_cast<char>(Serial.read());
    if (ch == '\r') {
      continue;
    }
    if (ch == '\n') {
      if (overflow) {
        Serial.println("ERR LINE_TOO_LONG");
      } else if (length > 0) {
        command[length] = '\0';
        reply(command);
      }
      length = 0;
      overflow = false;
    } else if (length < sizeof(command) - 1) {
      command[length++] = ch;
    } else {
      overflow = true;
    }
  }
}
