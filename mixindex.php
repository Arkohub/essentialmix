<?php
// Database connection settings
// $servername = "localhost";
// $username = "readonly_user";
// $password = "";
// $dbname = "Essential_DB";

// Create connection
$conn = new mysqli('localhost', 'readonly_user', '', 'Essential_DB');

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Get sort parameters from URL
$sortColumn = isset($_GET['sort']) ? $_GET['sort'] : 'MixID';
$sortOrder = isset($_GET['order']) ? $_GET['order'] : 'ASC';

// Get year filter parameters (as array)
$yearFilters = isset($_GET['years']) ? $_GET['years'] : [];

// Validate sort column to prevent SQL injection
$allowedColumns = ['MixID', 'Artist', 'Date', 'Year'];
if (!in_array($sortColumn, $allowedColumns)) {
    $sortColumn = 'MixID'; // Default if invalid column specified
}

// Validate sort order
if ($sortOrder != 'ASC' && $sortOrder != 'DESC') {
    $sortOrder = 'ASC';
}

// Build query with optional year filter
$whereClause = "";
if (!empty($yearFilters)) {
    // Sanitize input - ensure all values are integers
    $sanitizedYears = array_map('intval', $yearFilters);
    $yearsList = implode(',', $sanitizedYears);
    $whereClause = "WHERE Year IN ($yearsList)";
}

$sql = "SELECT * FROM MixList $whereClause ORDER BY $sortColumn $sortOrder";
$result = $conn->query($sql);

// Get unique years for the filter checkboxes
$yearsQuery = "SELECT DISTINCT Year FROM MixList ORDER BY Year DESC";
$yearsResult = $conn->query($yearsQuery);
$years = [];
if ($yearsResult->num_rows > 0) {
    while($yearRow = $yearsResult->fetch_assoc()) {
        $years[] = $yearRow['Year'];
    }
}

// Function to maintain checkboxes in URLs
function buildSortUrl($column, $currentSort, $currentOrder, $yearFilters) {
    $newOrder = ($currentSort == $column && $currentOrder == 'ASC') ? 'DESC' : 'ASC';
    $url = "?sort=$column&order=$newOrder";
    
    // Add years parameters if any are selected
    if (!empty($yearFilters)) {
        foreach ($yearFilters as $year) {
            $url .= "&years[]=$year";
        }
    }
    
    return $url;
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Essential Mix Archive</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color:rgb(22, 16, 29);
            color: white;
        }
        th a {
            color: white;
            text-decoration: none;
            display: block;
        }
        th a:hover {
            text-decoration: underline;
        }
        tr:hover {
            background-color: #f1f1f1;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .search-container {
            margin: 20px 0;
            text-align: center;
        }
        input[type=text] {
            padding: 10px;
            width: 300px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        .sort-icon {
            margin-left: 5px;
            font-size: 0.8em;
        }
        .filter-section {
            margin: 15px 0;
            text-align: center;
        }
        .filter-title {
            font-weight: bold;
            margin-bottom: 10px;
            display: block;
        }
        .year-filters {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
            margin-bottom: 15px;
        }
        .year-checkbox {
            display: inline-flex;
            align-items: center;
            margin-right: 5px;
            background-color: #f0f0f0;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
        }
        .year-checkbox:hover {
            background-color: #e0e0e0;
        }
        .year-checkbox input {
            margin-right: 5px;
        }
        .filter-buttons {
            margin-top: 10px;
        }
        button {
            padding: 8px 16px;
            background-color: rgb(22, 16, 29);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin: 0 5px;
        }
        button:hover {
            background-color: rgb(45, 35, 56);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Essential Mix Archive</h1>
        
        <div class="search-container">
            <input type="text" id="searchInput" onkeyup="searchTable()" placeholder="Search for mixes...">
        </div>
        
        <form id="yearFilterForm" method="get" action="">
            <!-- Hidden fields to preserve current sort -->
            <input type="hidden" name="sort" value="<?php echo $sortColumn; ?>">
            <input type="hidden" name="order" value="<?php echo $sortOrder; ?>">
            
            <div class="filter-section">
                <span class="filter-title">Filter by Year:</span>
                <div class="year-filters">
                    <?php foreach($years as $year): ?>
                    <label class="year-checkbox">
                        <input type="checkbox" name="years[]" value="<?php echo $year; ?>" 
                        <?php echo in_array($year, $yearFilters) ? 'checked' : ''; ?>>
                        <?php echo $year; ?>
                    </label>
                    <?php endforeach; ?>
                </div>
                <div class="filter-buttons">
                    <button type="submit">Apply Filters</button>
                    <button type="button" onclick="clearFilters()">Clear Filters</button>
                    <button type="button" onclick="selectAllYears()">Select All</button>
                    <button type="button" onclick="selectRecentYears(5)">Last 5 Years</button>
                </div>
            </div>
        </form>
        
        <table id="mixTable">
            <thead>
                <tr>
                    <th>
                        <a href="<?php echo buildSortUrl('MixID', $sortColumn, $sortOrder, $yearFilters); ?>">
                            ID
                            <?php if($sortColumn == 'MixID'): ?>
                                <span class="sort-icon"><?php echo $sortOrder == 'ASC' ? '▲' : '▼'; ?></span>
                            <?php endif; ?>
                        </a>
                    </th>
                    <th>
                        <a href="<?php echo buildSortUrl('Artist', $sortColumn, $sortOrder, $yearFilters); ?>">
                            Artist
                            <?php if($sortColumn == 'Artist'): ?>
                                <span class="sort-icon"><?php echo $sortOrder == 'ASC' ? '▲' : '▼'; ?></span>
                            <?php endif; ?>
                        </a>
                    </th>
                    <th>
                        <a href="<?php echo buildSortUrl('Date', $sortColumn, $sortOrder, $yearFilters); ?>">
                            Date
                            <?php if($sortColumn == 'Date'): ?>
                                <span class="sort-icon"><?php echo $sortOrder == 'ASC' ? '▲' : '▼'; ?></span>
                            <?php endif; ?>
                        </a>
                    </th>
                    <th>
                        <a href="<?php echo buildSortUrl('Year', $sortColumn, $sortOrder, $yearFilters); ?>">
                            Year
                            <?php if($sortColumn == 'Year'): ?>
                                <span class="sort-icon"><?php echo $sortOrder == 'ASC' ? '▲' : '▼'; ?></span>
                            <?php endif; ?>
                        </a>
                    </th>
                </tr>
            </thead>
            <tbody>
                <?php
                if ($result->num_rows > 0) {
                    // Output data of each row
                    while($row = $result->fetch_assoc()) {
                        echo "<tr>";
                        echo "<td>" . $row["MixID"] . "</td>";
                        echo "<td>" . $row["Artist"] . "</td>";
                        echo "<td>" . $row["Date"] . "</td>";
                        echo "<td>" . $row["Year"] . "</td>";
                        echo "</tr>";
                    }
                } else {
                    echo "<tr><td colspan='4'>No results found</td></tr>";
                }
                $conn->close();
                ?>
            </tbody>
        </table>
    </div>
    
    <script>
        function searchTable() {
            var input, filter, table, tr, td, i, txtValue;
            input = document.getElementById("searchInput");
            filter = input.value.toUpperCase();
            table = document.getElementById("mixTable");
            tr = table.getElementsByTagName("tr");
            
            for (i = 0; i < tr.length; i++) {
                // Skip header row
                if (i === 0) continue;
                
                var found = false;
                // Loop through all table cells in this row
                for (var j = 0; j < tr[i].cells.length; j++) {
                    td = tr[i].cells[j];
                    if (td) {
                        txtValue = td.textContent || td.innerText;
                        if (txtValue.toUpperCase().indexOf(filter) > -1) {
                            found = true;
                            break;
                        }
                    }
                }
                tr[i].style.display = found ? "" : "none";
            }
        }
        
        function clearFilters() {
            window.location.href = "?sort=<?php echo $sortColumn; ?>&order=<?php echo $sortOrder; ?>";
        }
        
        function selectAllYears() {
            var checkboxes = document.querySelectorAll('input[name="years[]"]');
            for (var i = 0; i < checkboxes.length; i++) {
                checkboxes[i].checked = true;
            }
            document.getElementById('yearFilterForm').submit();
        }
        
        function selectRecentYears(count) {
            // First uncheck all
            var checkboxes = document.querySelectorAll('input[name="years[]"]');
            for (var i = 0; i < checkboxes.length; i++) {
                checkboxes[i].checked = false;
            }
            
            // Then check only the most recent 'count' years
            for (var i = 0; i < Math.min(count, checkboxes.length); i++) {
                checkboxes[i].checked = true;
            }
            
            document.getElementById('yearFilterForm').submit();
        }
    </script>
</body>
</html>