setwd("D:/41617568B/Downloads")

library(tidyverse)
library(dplyr)
library(readr)
library(lubridate)
library(plm)      
library(ggplot2)  
library(lmtest)
library(sandwich)

# Dades Estació Bicing i barris ----
bicing_data <- read_csv("Informacio_Estacions_Bicing_2025.csv")

estacions <- bicing_data %>%
  mutate(
    temp = str_extract(cross_street, "^[^;]+"),
    district_code = str_extract(temp, "^\\d+"),
    district_name = str_extract(temp, "(?<=-).*(?=/)"),
    codi_barri = str_extract(temp, "(?<=/)\\d+"),
    neighborhood_name = str_extract(temp, "(?<=/)\\d+-(.*)$") %>% 
      str_replace("^\\d+-", "")
  ) %>% 
  mutate(codi_barri = as.numeric(codi_barri)) %>% 
  select(codi_barri, neighborhood_name, lat, lon, station_id)

library(writexl)
write_xlsx(estacions, "estacions.xlsx")

# Dades festes barri ----
dades_barri <- read.csv("dades_barris.csv")
estacions_joined <- estacions %>%
  left_join(dades_barri, by = "codi_barri") 

# Focus only on 2023 dates
estacions_joined <- estacions_joined %>%
  mutate(
    inici_2023 = as.Date(inici_2023, format = "%m/%d/%Y"),
    fi_2023 = as.Date(fi_2023, format = "%m/%d/%Y")
  )

# Check for NA dates in 2023
print(paste("NAs in 2023 date columns:", sum(is.na(estacions_joined$inici_2023) | is.na(estacions_joined$fi_2023))))

# Create date range for 2023 only
start_date <- as.Date("2023-01-01")
end_date <- as.Date("2023-12-31")
all_days_2023 <- seq.Date(from = start_date, to = end_date, by = "day")

# Create the expanded dataset for 2023 only
expanded_data <- expand.grid(
  date = all_days_2023,
  station_id = unique(estacions_joined$station_id)
) %>%
  as_tibble() %>%
  mutate(
    year = year(date),
    month = month(date),
    day = day(date)
  )

# Join station to barri information
station_barri <- estacions_joined %>%
  select(station_id, codi_barri) %>%
  distinct()

expanded_data <- expanded_data %>%
  left_join(station_barri, by = "station_id")

# Join festa barri information for 2023 only
expanded_data <- expanded_data %>%
  left_join(
    estacions_joined %>% 
      select(codi_barri, inici_2023, fi_2023) %>%
      distinct(),
    by = "codi_barri"
  )

# Create festa_barri indicator variable for 2023
expanded_data <- expanded_data %>%
  mutate(
    festa_barri = ifelse(!is.na(inici_2023) & !is.na(fi_2023) & 
                           date >= inici_2023 & date <= fi_2023, 1, 0)
  )

final_dataset <- expanded_data %>%
  select(year, month, day, station_id, codi_barri, festa_barri, date)

# Filter to ensure only 2023 data
final_dataset <- final_dataset %>%
  filter(year == 2023)

# Unir final_dataset amb les dades extretes de bicing per fer el model ----
dades_bici <- read.csv("df_result_with_year_2020_2023_v2.csv")

# Filter for only 2023 data in dades_bici
dades_bici <- dades_bici %>%
  filter(year == 2023)

# Make sure station_id is of the same type in both datasets
dades_bici$station_id <- as.numeric(dades_bici$station_id)

# Join the datasets
bicing_data_merged <- final_dataset %>%
  inner_join(dades_bici, by = c("station_id", "year", "month", "day")) %>%
  select("station_id", "year", "month", "day", "codi_barri", "ctx.0", "festa_barri", "date") %>%
  mutate(festa_barri = ifelse(is.na(festa_barri), 0, festa_barri)) %>%
  filter(!is.na(ctx.0))

# Fixed Effects Model ----

bicing_data_merged$date <- as.Date(bicing_data_merged$date)

# Create variables for day of week and weekend
bicing_data_merged$day_of_week <- weekdays(bicing_data_merged$date)
bicing_data_merged$is_weekend <- ifelse(bicing_data_merged$day_of_week %in% c("Saturday", "Sunday"), 1, 0)

# Panel data fixed effects model
# ctx.0 represents available docks, which is inversely related to bicycle demand
# More available docks = fewer bicycles in use
panel_model <- plm(ctx.0 ~ festa_barri + is_weekend + as.factor(month),
                   data = bicing_data_merged,
                   index = c("station_id", "date"),
                   model = "within")

# Get robust standard errors
robust_se <- vcovHC(panel_model, type = "HC1")
coeftest(panel_model, vcov = robust_se)

# If you want to analyze by neighborhood (barri)
neighborhood_model <- plm(ctx.0 ~ festa_barri + is_weekend + as.factor(month),
                          data = bicing_data_merged,
                          index = c("codi_barri", "date"),
                          model = "within")

coeftest(neighborhood_model, vcov = vcovHC(neighborhood_model, type = "HC1"))

interaction_model <- plm(ctx.0 ~ festa_barri*is_weekend + as.factor(month),
                         data = bicing_data_merged,
                         index = c("station_id", "date"),
                         model = "within")
library(ggplot2)

# Aggregate data ----
avg_by_celebration <- bicing_data_merged %>%
  group_by(festa_barri, station_id) %>%
  summarize(avg_available_docks = mean(ctx.0, na.rm = TRUE))

# Create a vector to map codi_barri to neighborhood names
neighborhood_mapping <- c(
  "05" = "el Fort Pienc",
  "04" = "Sant Pere, Santa Caterina i la Ribera",
  "12" = "la Marina del Prat Vermell",
  "03" = "la Barceloneta",
  "67" = "la Vila Olímpica del Poblenou",
  "07" = "la Dreta de l'Eixample",
  "66" = "el Parc i la Llacuna del Poblenou",
  "06" = "la Sagrada Família",
  "64" = "el Camp de l'Arpa del Clot",
  "70" = "el Besòs i el Maresme",
  "02" = "el Barri Gòtic",
  "01" = "el Raval",
  "09" = "la Nova Esquerra de l'Eixample",
  "10" = "Sant Antoni",
  "08" = "l'Antiga Esquerra de l'Eixample",
  "19" = "les Corts",
  "26" = "Sant Gervasi - Galvany",
  "31" = "la Vila de Gràcia",
  "32" = "el Camp d'en Grassot i Gràcia Nova",
  "73" = "la Verneda i la Pau",
  "72" = "Sant Martí de Provençals",
  "71" = "Provençals del Poblenou",
  "68" = "el Poblenou",
  "69" = "Diagonal Mar i el Front Marítim del Poblenou",
  "63" = "Navas",
  "62" = "el Congrés i els Indians",
  "61" = "la Sagrera",
  "60" = "Sant Andreu",
  "59" = "el Bon Pastor",
  "57" = "la Trinitat Vella",
  "55" = "Ciutat Meridiana",
  "37" = "el Carmel",
  "36" = "la Font d'en Fargues",
  "45" = "Porta",
  "44" = "Vilapicina i la Torre Llobeta",
  "43" = "Horta",
  "42" = "la Clota",
  "41" = "la Vall d'Hebron",
  "28" = "Vallcarca i els Penitents",
  "30" = "la Salut",
  "25" = "Sant Gervasi - la Bonanova",
  "24" = "les Tres Torres",
  "23" = "Sarrià",
  "21" = "Pedralbes",
  "20" = "la Maternitat i Sant Ramon",
  "14" = "la Font de la Guatlla",
  "13" = "la Marina de Port",
  "11" = "el Poble-sec"
)

# Replace codi_barri with the corresponding neighborhood name
avg_by_celebration <- bicing_data_merged %>%
  group_by(festa_barri, codi_barri, station_id) %>%
  summarize(avg_available_docks = mean(ctx.0, na.rm = TRUE))


# Load the necessary library
library(ggplot2)

# Plot the data with individual plots for each neighborhood
ggplot(avg_by_celebration, aes(x = festa_barri, y = avg_available_docks, fill = festa_barri)) +
  geom_bar(stat = "identity") +
  facet_wrap(~ codi_barri, scales = "free_y") +  # Create individual plots for each neighborhood
  labs(
    title = "Average Available Docks by Neighborhood and Celebration",
    x = "Celebration",
    y = "Average Available Docks",
    fill = "Celebration"
  ) +
  theme(axis.text.x = element_text(angle = 45, hjust = 1)) + # Rotate x-axis labels for better readability
  theme_minimal() # Optional: to apply a cleaner theme

ggplot(avg_by_celebration, aes(x = factor(festa_barri), y = avg_available_docks, fill = factor(festa_barri))) +
  geom_bar(stat = "identity") +
  labs(x = "Celebration (1 = Yes, 0 = No)", y = "Average Available Docks", 
       title = "Bicycle Dock Availability During Celebrations") +
  theme_minimal()

save(excel, file = avg_by_celebration)

avg_by_celebration <- estacions %>%
  left_join(avg_by_celebration, by = "station_id")
            
library(readxl)
write_xlsx(avg_by_celebration, path = "avg_by_celebration.xlsx")


df_clean <- df %>%
  filter(!is.na(avg_available_docks), !is.na(festa_barri), !is.na(neighborhood_name))

dock_summary <- df_clean %>%
  group_by(neighborhood_name, festa_barri) %>%
  summarise(mean_available_docks = mean(avg_available_docks, na.rm = TRUE)) %>%
  mutate(festa_status = ifelse(festa_barri == 1, "Si", "No"))

# Create a grouped bar chart
ggplot(dock_summary, aes(x = neighborhood_name, y = mean_available_docks, fill = festa_status)) +
  geom_bar(stat = "identity", position = position_dodge(width = 0.9)) +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1,), 
        legend.position = "left") +
  labs(title = "Promedio de la disponibilidad de las bicicletas por barrios de Barcelona i si estan en fiestas (2023)",
       x = "Barrios",
       y = "Disponibilidad de Docks (%)",
       fill = "El barrio esta en fiestas?") +
  scale_fill_manual(values = c("Si" = "#FF9999", "No" = "#99CCFF"))

# Create a faceted plot to show the same data differently
ggplot(dock_summary, aes(x = neighborhood_name, y = mean_available_docks, fill = festa_status)) +
  geom_bar(stat = "identity") +
  facet_wrap(~festa_status) +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
  labs(title = "Average Available Docks by Neighborhood and Holiday Status",
       x = "Neighborhood",
       y = "Average Available Docks") +
  scale_fill_manual(values = c("Festes al barri" = "#FF9999", "No festes al barri" = "#99CCFF"))

# Create a paired plot to show the difference more clearly
# First, reshape the data
dock_wide <- dock_summary %>%
  pivot_wider(names_from = festa_barri, values_from = mean_available_docks, names_prefix = "festa_") %>%
  mutate(difference = festa_1 - festa_0)

# Then create a plot showing the difference
ggplot(dock_wide, aes(x = neighborhood_name, y = difference)) +
  geom_bar(stat = "identity", fill = "#66AAFF") +
  geom_hline(yintercept = 0, linetype = "dashed", color = "red") +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
  labs(title = "Difference in Average Available Docks (Holiday - Non-Holiday)",
       x = "Neighborhood",
       y = "Difference in Available Docks") +
  scale_y_continuous(labels = scales::percent_format(scale = 1))

# Create a boxplot to show the distribution of available docks
ggplot(df_clean, aes(x = factor(festa_barri), y = avg_available_docks, fill = factor(festa_barri))) +
  geom_boxplot() +
  facet_wrap(~neighborhood_name, scales = "free_y") +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
  labs(title = "Distribution of Available Docks by barris i si hi ha festes",
       x = "Festes al barri?",
       y = "Average Available Docks",
       fill = "Festes al barri?") +
  scale_fill_manual(values = c("0" = "#99CCFF", "1" = "#FF9999"),
                    labels = c("0" = "No = 0", "1" = "Si = 1"))

ggplot(df_clean, aes(x = factor(festa_barri), y = avg_available_docks, fill = factor(festa_barri))) +
  geom_boxplot() +
  theme_minimal() +
  labs(title = "Distribución de Docks Disponibles por Fiestas de Barrio (2023)",
       x = "Estado de Fiesta",
       y = "Promedio de Docks Disponibles",
       fill = "Fiesta de Barrio") +
  scale_x_discrete(labels = c("0" = "Sin Fiesta", "1" = "Con Fiesta")) +
  scale_fill_manual(values = c("0" = "#99CCFF", "1" = "#FF9999"),
                    labels = c("0" = "Sin Fiesta", "1" = "Con Fiesta"))

