#include "led-matrix.h"
#include "graphics.h"
#include <curl/curl.h>
#include <nlohmann/json.hpp>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <iostream>
#include <string>
#include <array>

//URL is hardcoded for fetching leaderboard data

// For convenience
using namespace rgb_matrix;
using json = nlohmann::json;

// Global for interrupt handling
static volatile bool interrupt_received = false;
static void InterruptHandler(int signo) {
  interrupt_received = true;
}

// Helper callback for libcurl to store fetched data into a std::string
static size_t WriteCallback(void * contents, size_t size, size_t nmemb, void * userp) {
  ((std::string * ) userp) -> append((char * ) contents, size * nmemb);
  return size * nmemb;
}

// Function to perform HTTP GET on the specified URL
std::string FetchLeaderboard(const std::string & url) {
  CURL * curl = curl_easy_init();
  std::string readBuffer;

  if (curl) {
    // Set options for curl
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, & readBuffer);

    // Perform the request
    CURLcode res = curl_easy_perform(curl);
    if (res != CURLE_OK) {
      fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
    }
    curl_easy_cleanup(curl);
  }

  return readBuffer;
}

// Function to draw leaderboard data on the LED matrix
void DisplayLeaderboard(RGBMatrix * canvas,
  const rgb_matrix::Font & font,
    const std::string & leaderboard_data) {
  json response;
  json leaderboard;
  int month = -1; // Initialize to -1 to indicate not set
  try {
    response = json::parse(leaderboard_data);
    if (response.contains("leaderboard")) {
      leaderboard = response["leaderboard"];
    } else {
      fprintf(stderr, "JSON does not contain 'leaderboard' array\n");
      return;
    }
    if (response.contains("month")) {
      month = response["month"];
    }
  } catch (...) {
    fprintf(stderr, "Error parsing JSON data\n");
    return;
  }

  // Clear the matrix
  canvas -> Clear();

  // White text color
  Color text_color(255, 255, 255);
  Color header_color(255, 191, 0);

  int x = 1;
  int y = font.baseline() + 2;

  // Title
  DrawText(canvas, font, x, y, header_color, nullptr, "   LeetCode Leaderboard", 0);
  y += font.height() + 2;

  // Optional header row
  DrawText(canvas, font, x, y, text_color, nullptr, "Username           Points", 0);
  y += font.height() + 2;

  // Loop over the array, displaying username & points
  int rank = 1;
  for (auto & item: leaderboard) {
    std::string username = "unknown";
    int points = 0;

    try {
      if (item.contains("username") && item["username"].is_string()) {
        username = item["username"];
      }
      if (item.contains("points") && item["points"].is_number_integer()) {
        points = item["points"];
      }
    } catch (const std::exception & e) {
      fprintf(stderr, "Error parsing leaderboard item: %s\n", e.what());
    }

    if (username.length() > 10) {
      username = username.substr(0, 10); // Cut to 10 characters max
    }

    // Display rank. If you don't want rank, just remove `%2d.` from the format
    char buffer[64];
    snprintf(buffer, sizeof(buffer), "%2d. %-10s %10d",
      rank, username.c_str(), points);
    if (rank == 1) {
      text_color = Color(255, 191, 0);
    } else if (rank == 2) {
      text_color = Color(255, 0, 0);
    } else if (rank == 3) {
      text_color = Color(126, 147, 255);
    } else {
      text_color = Color(255, 255, 255);
    }

    DrawText(canvas, font, x, y, text_color, nullptr, buffer, 0);
    y += font.height() + 2;

    rank++;
    if (rank > 10) {
      // If you only want top 5, break now
      break;
    }
  }
  
  // Only display month if it was successfully retrieved from JSON
  if (month >= 0 && month <= 11) {
    // Map month number (0-11) to month name
    constexpr std::array<const char*, 12> month_names = {
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    };

    text_color = Color(255, 191, 0);
    std::string month_text = "     Month: " + std::string(month_names[month]);
    DrawText(canvas, font, x, y, text_color, nullptr, month_text.c_str(), 0);
  }
}

int main(int argc, char * argv[]) {
  //---------------------------------------------------------------------------
  // 1. Parse command-line flags for the LED panel
  //---------------------------------------------------------------------------
  RGBMatrix::Options matrix_options;
  // If you're using an Adafruit HAT, set:
  matrix_options.hardware_mapping = "adafruit-hat";

  rgb_matrix::RuntimeOptions runtime_opt;
  if (!ParseOptionsFromFlags( & argc, & argv, &
      matrix_options, & runtime_opt)) {
    fprintf(stderr, "Couldn't parse LED matrix options.\n");
    return 1;
  }

  //---------------------------------------------------------------------------
  // 2. Load the font
  //---------------------------------------------------------------------------
  const char * bdf_font_file = "./5x7.bdf";
  rgb_matrix::Font font;
  if (!font.LoadFont(bdf_font_file)) {
    fprintf(stderr, "Couldn't load font '%s'\n", bdf_font_file);
    return 1;
  }

  //---------------------------------------------------------------------------
  // 3. Create the matrix & set up signal handling
  //---------------------------------------------------------------------------
  RGBMatrix * canvas = CreateMatrixFromOptions(matrix_options, runtime_opt);
  if (!canvas) {
    return 1;
  }

  signal(SIGINT, InterruptHandler);
  signal(SIGTERM, InterruptHandler);

  //---------------------------------------------------------------------------
  // 4. Continuously fetch and display leaderboard
  //---------------------------------------------------------------------------
  const std::string api_url = "http://localhost:8000/";

  while (!interrupt_received) {
    // Fetch JSON
    std::string leaderboard_data = FetchLeaderboard(api_url);
    // Display
    DisplayLeaderboard(canvas, font, leaderboard_data);

    // Sleep 300 seconds, or break if interrupted
    for (int i = 0; i < 300 && !interrupt_received; ++i) {
      sleep(1);
    }
  }

  //---------------------------------------------------------------------------
  // 5. Cleanup
  //---------------------------------------------------------------------------
  canvas -> Clear();
  delete canvas;

  return 0;
}
