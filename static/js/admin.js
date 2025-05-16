// Функция для фильтрации таблицы
function filterTable(tableId, searchId) {
  const table = document.getElementById(tableId);
  const search = document.getElementById(searchId);
  const filter = search.value.toLowerCase();
  const rows = table.getElementsByTagName('tr');

  for (let i = 1; i < rows.length; i++) {
    const row = rows[i];
    const cells = row.getElementsByTagName('td');
    let found = false;

    for (let j = 0; j < cells.length; j++) {
      const cell = cells[j];
      if (cell.textContent.toLowerCase().indexOf(filter) > -1) {
        found = true;
        break;
      }
    }

    row.style.display = found ? '' : 'none';
  }
}

// Инициализация графиков
function initQualityChart() {
  const ctx = document.getElementById('qualityChart').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: qualityData.labels,
      datasets: [{
        label: 'Общая оценка',
        data: qualityData.scores,
        borderColor: '#007bff',
        tension: 0.1
      }, {
        label: 'Полезные ответы',
        data: qualityData.helpful,
        borderColor: '#28a745',
        tension: 0.1
      }, {
        label: 'Точность',
        data: qualityData.accuracy,
        borderColor: '#ffc107',
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          max: 100
        }
      }
    }
  });
}

function initUsageChart() {
  const ctx = document.getElementById('usageChart').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: usageData.labels,
      datasets: [{
        label: 'Запросов в час',
        data: usageData.requests,
        borderColor: '#007bff',
        tension: 0.1
      }, {
        label: 'Среднее время ответа',
        data: usageData.responseTime,
        borderColor: '#dc3545',
        tension: 0.1,
        yAxisID: 'y1'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          position: 'left'
        },
        y1: {
          beginAtZero: true,
          position: 'right',
          grid: {
            drawOnChartArea: false
          }
        }
      }
    }
  });
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
  // Инициализация графиков при открытии модальных окон
  document.querySelectorAll('.apple-modal').forEach(modal => {
    modal.addEventListener('show.bs.modal', function() {
      if (this.id === 'qualityModal') {
        initQualityChart();
      } else if (this.id === 'usageModal') {
        initUsageChart();
      }
    });
  });
}); 