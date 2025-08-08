document.addEventListener('DOMContentLoaded', () => {
    let activeTooltip = null; // 現在表示中のツールチップを追跡

    // ツールチップの位置を動的に調整する関数
    function adjustTooltipPosition(dayDiv, tooltip) {
        tooltip.style.left = '';
        tooltip.style.right = '';
        tooltip.style.top = '';
        tooltip.style.bottom = '';

        const dayRect = dayDiv.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        const viewportWidth = window.innerWidth || document.documentElement.clientWidth;
        const viewportHeight = window.innerHeight || document.documentElement.clientHeight;

        // デフォルト: 上に表示
        let position = 'top';
        tooltip.style.bottom = '125%';
        tooltip.style.left = '50%';
        tooltip.style.transform = 'translateX(-50%)';

        // ツールチップの新しい位置を計算
        const newTooltipRect = tooltip.getBoundingClientRect();

        // 右端にはみ出す場合
        if (newTooltipRect.right > viewportWidth - 10) {
            tooltip.style.left = 'auto';
            tooltip.style.right = `-${dayRect.width / 2}px`;
            tooltip.style.transform = 'none';
        }
        // 左端にはみ出す場合
        if (newTooltipRect.left < 10) {
            tooltip.style.left = `-${dayRect.width / 2}px`;
            tooltip.style.right = 'auto';
            tooltip.style.transform = 'none';
        }
        // 下端にはみ出す場合（上に収まらない場合、下に表示）
        if (newTooltipRect.bottom > viewportHeight - 10) {
            position = 'bottom';
            tooltip.style.bottom = 'auto';
            tooltip.style.top = '125%';
            tooltip.classList.remove('top');
            tooltip.classList.add('bottom');
        } else {
            tooltip.classList.remove('bottom');
            tooltip.classList.add('top');
        }

        // 上端にはみ出す場合（下に表示）
        if (newTooltipRect.top < 10) {
            position = 'bottom';
            tooltip.style.bottom = 'auto';
            tooltip.style.top = '125%';
            tooltip.classList.remove('top');
            tooltip.classList.add('bottom');
        }

        return position;
    }

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

                    const firstDayOfMonth = new Date(year, month - 1, 1).getDay();
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
                            tooltip.classList.add('tooltip', 'top');
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

                            // ホバーでツールチップ表示（PC）
                            dayDiv.addEventListener('mouseenter', () => {
                                if (!activeTooltip) {
                                    adjustTooltipPosition(dayDiv, tooltip);
                                    tooltip.classList.add('tooltip-active');
                                    activeTooltip = tooltip;
                                }
                            });

                            dayDiv.addEventListener('mouseleave', () => {
                                if (activeTooltip === tooltip) {
                                    tooltip.classList.remove('tooltip-active');
                                    activeTooltip = null;
                                }
                            });

                            // タップでツールチップ表示（スマホ）
                            dayDiv.addEventListener('click', (e) => {
                                e.preventDefault();
                                e.stopPropagation();

                                if (activeTooltip && activeTooltip !== tooltip) {
                                    activeTooltip.classList.remove('tooltip-active');
                                }

                                const isActive = tooltip.classList.contains('tooltip-active');
                                if (isActive) {
                                    tooltip.classList.remove('tooltip-active');
                                    activeTooltip = null;
                                } else {
                                    adjustTooltipPosition(dayDiv, tooltip);
                                    tooltip.classList.add('tooltip-active');
                                    activeTooltip = tooltip;
                                }
                            });
                        }
                        dayGridDiv.appendChild(dayDiv);
                    }
                    monthCalendarDiv.appendChild(dayGridDiv);
                    monthGridDiv.appendChild(monthCalendarDiv);
                }
                yearCalendarDiv.appendChild(monthGridDiv);
                calendarContainer.appendChild(yearCalendarDiv);
            }

            // 背景をクリックしたときにツールチップを隠す
            document.addEventListener('click', (e) => {
                if (activeTooltip && !e.target.closest('.day')) {
                    activeTooltip.classList.remove('tooltip-active');
                    activeTooltip = null;
                }
            });
        })
        .catch(error => console.error('Error fetching calendar data:', error));
});