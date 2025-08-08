document.addEventListener('DOMContentLoaded', () => {
    fetch('data/processed/calendar_data.json')
        .then(response => response.json())
        .then(data => {
            const calendarContainer = document.getElementById('calendar-container');
            const years = {};

            // Group data by year
            for (const dateStr in data) {
                const year = dateStr.substring(0, 4);
                if (!years[year]) {
                    years[year] = {};
                }
                const month = parseInt(dateStr.substring(5, 7), 10);
                if (!years[year][month]) {
                    years[year][month] = [];
                }
                years[year][month].push(data[dateStr]);
            }

            for (const year in years) {
                const yearCalendarDiv = document.createElement('div');
                yearCalendarDiv.classList.add('year-calendar');
                yearCalendarDiv.innerHTML = `<h2 class="year-title">${year}年</h2>`;

                const monthGridDiv = document.createElement('div');
                monthGridDiv.classList.add('month-grid');

                for (let month = 1; month <= 12; month++) {
                    const monthCalendarDiv = document.createElement('div');
                    monthCalendarDiv.classList.add('month-calendar');
                    monthCalendarDiv.innerHTML = `<h3 class="month-title">${month}月</h3>`;

                    const weekdaysDiv = document.createElement('div');
                    weekdaysDiv.classList.add('weekdays');
                    ['日', '月', '火', '水', '木', '金', '土'].forEach(day => {
                        const weekdaySpan = document.createElement('span');
                        weekdaySpan.textContent = day;
                        weekdaysDiv.appendChild(weekdaySpan);
                    });
                    monthCalendarDiv.appendChild(weekdaysDiv);

                    const dayGridDiv = document.createElement('div');
                    dayGridDiv.classList.add('day-grid');

                    const firstDayOfMonth = new Date(year, month - 1, 1).getDay(); // 0 for Sunday, 1 for Monday...
                    for (let i = 0; i < firstDayOfMonth; i++) {
                        const emptyDay = document.createElement('div');
                        emptyDay.classList.add('day', 'empty');
                        dayGridDiv.appendChild(emptyDay);
                    }

                    const daysInMonth = new Date(year, month, 0).getDate();
                    for (let day = 1; day <= daysInMonth; day++) {
                        const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                        const dayData = data[dateStr];

                        const dayDiv = document.createElement('div');
                        dayDiv.classList.add('day');
                        dayDiv.textContent = day;

                        if (dayData) {
                            if (dayData.impact_level === 'High') {
                                dayDiv.classList.add('high-demand');
                            } else if (dayData.impact_level === 'Medium') {
                                dayDiv.classList.add('medium-demand');
                            } else {
                                dayDiv.classList.add('low-demand');
                            }

                            // Tooltip
                            const tooltip = document.createElement('div');
                            tooltip.classList.add('tooltip');
                            let tooltipContent = `<strong>日付: ${dayData.date}</strong><br>`;
                            tooltipContent += `<p>需要スコア: ${dayData.demand_score.toFixed(2)}</p>`;
                            tooltipContent += `<p>影響度レベル: ${dayData.impact_level}</p>`;

                            if (dayData.monthly_trend_score) {
                                tooltipContent += `<p>月間トレンドスコア: ${dayData.monthly_trend_score.toFixed(2)}</p>`;
                            }

                            if (dayData.is_holiday) {
                                tooltipContent += `<p>祝日: ${dayData.holiday_name}</p>`;
                            }

                            if (dayData.events.length > 0) {
                                tooltipContent += `<p>イベント:</p><ul>`;
                                dayData.events.forEach(event => {
                                    tooltipContent += `<li>${event.subject} (${event.event_type}) - ${event.estimated_attendees}人</li>`;
                                });
                                tooltipContent += `</ul>`;
                            }
                            tooltip.innerHTML = tooltipContent;
                            dayDiv.appendChild(tooltip);
                        }
                        dayGridDiv.appendChild(dayDiv);
                    }
                    monthCalendarDiv.appendChild(dayGridDiv);
                    monthGridDiv.appendChild(monthCalendarDiv);
                }
                yearCalendarDiv.appendChild(monthGridDiv);
                calendarContainer.appendChild(yearCalendarDiv);
            }
        })
        .catch(error => console.error('Error fetching calendar data:', error));
});