#
# This is a Shiny web application. You can run the application by clicking
# the 'Run App' button above.
#
# Find out more about building applications with Shiny here:
#
#    http://shiny.rstudio.com/
#

library(shiny)
library(tidyverse)
library(data.table)
library(plotly)
library(shinyWidgets)

# Data preparations 
data <- readRDS("./data/data_fp.RData")
data1 <- data[, .("value" = sum(value)), 
              by = .(country_name, year, Accounting, Emission)]
data1[, "value_indexed (2005 = 100)" := 100 * (value / value[11]), 
      by = .(country_name, Accounting, Emission)]
data2 <- data[Accounting == "Consumption"]
data2[, "value_indexed (2005 = 100)" := 100 * (value / value[11]), 
      by = .(country_name, Type, Emission)]


## UI
# Use a fluid Bootstrap layout
ui <- fluidPage(
  # Give the page a title
  titlePanel("Footprint Timeseries"),
  # Generate a row with a sidebar
  sidebarLayout(
    # Define the sidebar
    sidebarPanel(
      # # Input file
      # fileInput("file", "Upload updated feather file", 
      #           accept = ".feather"), 

      # Input type of plot
      radioButtons("type", "Type of plot: ", 
                   c("Consumption-based VS Production-based footprints (line plot)" = "mode1", 
                     "Consumption-based split by Domestic + Abroad + Direct (line plot)" = "mode2", 
                     "Consumption-based split by Domestic + Abroad + Direct (stacked area plot)" = "mode3")),
      # Input type of footprint
      selectInput("fp", "Type of footprint:", 
                  choices = unique(data$Emission), 
                  selected = unique(data$Emission)[5]),
      # Input y-axis log scale
      radioButtons("logy", "Y-axis:", c("Linear" = "linear", 
                                        "Logarithmic" = "log", 
                                        "Indexed (2005 = 100)" = "indexed")),
      # radioButtons("fixedy", "Fixed Y-axis (only relevant for stacked area plot)?", c("TRUE" = "fixed", 
      #                                           "FALSE" = "free_y")),
      materialSwitch("fixedy", "Fixed Y-axis (only relevant for stacked area plot)?", 
                     value = TRUE),
      # Input indexed time series 
      #materialSwitch("indexed", "Index time series (2005 = 100)"),
      # Input region included
      actionLink("selectall", "Select all regions"),
      checkboxGroupInput("region", "Region:", 
                         choices = unique(data$country_name), 
                         selected = c("Germany", "China", "France", 
                                      "United States")),
      width = 3
    ),
    # Create a spot for the barplot
    mainPanel(
      plotOutput("FootprintTimeseries", width = "100%")  
    )
    
  )
)

## Server

# Define a server for the Shiny app
server <- function(input, output, session) {
  # update input "region" if select_all was pressed
  observe({
    if(input$selectall == 0) return(NULL) 
    else if (input$selectall%%2 == 0) {
      updateCheckboxGroupInput(session, "region", "Region:", 
                               choices=unique(data$country_name))  
    } else {
      updateCheckboxGroupInput(session, "region", "Region:", 
                               choices=unique(data$country_name), 
                               selected = unique(data$country_name))
    }
  })
  
  
  # Fill in the spot we created for a plot
  output$FootprintTimeseries <- renderPlot({
    y_value <- ifelse((input$logy) == "indexed", "`value_indexed (2005 = 100)`", "value")
   # print(y_value)
    if (input$type == "mode1") {
      p <- data1[Emission == input$fp & country_name %in% input$region] %>% 
        ggplot(aes(x = year, col = country_name, linetype = Accounting)) + 
        geom_line(aes_string(y = y_value))  
    } else if (input$type == "mode2") {
      p <- data2[Emission == input$fp & country_name %in% input$region] %>% 
        ggplot(aes(x = year, col = country_name, linetype = Type)) + 
        geom_line(aes_string(y = y_value))
    } else if (input$type == "mode3") {
      p <- data2[Emission == input$fp & country_name %in% input$region] %>% 
        ggplot(aes(x = year, y = value)) + 
        geom_area(aes(col = Type, fill = Type), 
                  position = "stack") 
      if (length(input$region) > 0) {
       p <- p + facet_wrap(~country_name, 
                           scales = ifelse(isTRUE(input$fixedy), "fixed", "free_y"))
      }
    }
    if (input$logy == "log") p <- p + scale_y_continuous(trans='log10') + ylab("log value")
    p + 
      ggtitle(input$fp) + 
      theme_bw()# + 
      # theme(legend.position = "bottom", legend.box = "horizontal", 
      #       legend.direction = "vertical")
  }, height = "auto")
}

shinyApp(ui, server)