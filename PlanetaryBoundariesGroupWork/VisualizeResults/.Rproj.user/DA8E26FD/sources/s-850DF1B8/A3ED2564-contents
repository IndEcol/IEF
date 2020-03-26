#' 
#' 
#'  
#' @author Simon Schulte
#' Date: 2020-03-25 11:25:53
#' 
#' Content:
#'  


############################################################################## # 
##### load packages ############################################################
############################################################################## # 

library(data.table)
library(tidyverse)
library(my.utils)

############################################################################## # 
##### settings #################################################################
############################################################################## # 
path2data <- "./data/"
options("datatable.print.class" = TRUE)

EB3_metadata <- readRDS(file.path(path2data, "EB3_metadata.RData"))
EB36_characterization <- fread(file.path(path2data, "Characterization_EB36.csv"))
EB36_characterization <- EB36_characterization[24:.N,]
############################################################################## # 
##### load data #############################################################
############################################################################## # 
data <- read_feather(file.path(path2data, "TimeSeries.feather")) %>% 
  as.data.table

data <- melt(data, id.vars = c("Region", "Emission", "Type"), 
             variable.factor = FALSE, variable.name = "year")
data[, year := as.integer(year)]
data[, "Accounting" := ifelse(Type == "Territorial", "Territorial", "Consumption")]
data[, Emission := trimws(Emission)]

# 1. Calculate Characterization factor (footprints from emission) --------------
data_wide <- dcast(data, Region + Type + year + Accounting ~ Emission)
setcolorder(data_wide, neworder = c(colnames(data_wide)[1:4], 
                                    EB36_characterization$`Emission Type`))

data_fp <- as.matrix(data_wide[,-(1:4)]) %*% as.matrix(EB36_characterization[,-1])
data_fp <- data.table(data_wide[,1:4], data_fp)
data_fp <- melt(data_fp, id.vars = c("Region", "Type", "year", "Accounting"), 
                variable.name = "Emission")

# 1b. Add N + P footprints -----------------------------------------------------
NP_footprints <- c("N - agriculture - water", "P - agriculture - soil",
                   "P - agriculture - water", "Pxx - agriculture - soil", 
                   "N - waste - water", "P - waste - water") 

data_fp <- rbind(data_fp, data[Emission %in% NP_footprints])

# 2. Add more information for countries ----------------------------------------
data_fp <- merge(data_fp, EB3_metadata$regions[, c("country_code1", "country_name")], 
                 by.x = "Region", by.y = "country_code1")

saveRDS(data_fp, "./visualize_planetary_boundaries/data/data_fp.RData")

# THE END ---------------------------------------------------------------------
