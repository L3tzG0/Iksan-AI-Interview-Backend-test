import type { FC } from 'react';
import type { FilterControlsProps } from '../../types/teacherDashboard';
import { FilterIcon, SortIcon, ChartIcon } from '../icons';

const FilterControls: FC<FilterControlsProps> = ({
  gradeFilter,
  gradeOptions = [],
  sortOption,
  goalFilter,
  onGradeChange,
  onSortChange,
  onGoalChange,
  compact,
  showGrade = false,
  showGoal = true,
}) => (
  <div className={`flex flex-wrap gap-3 items-center ${compact ? 'justify-end' : ''}`}>
    {showGrade && (
      <label className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 border border-slate-200 rounded-full font-semibold text-xs">
        <ChartIcon className="w-4 h-4 text-primary" />
        <select
          value={gradeFilter === 'all' ? 'all' : gradeFilter}
          onChange={(e) => onGradeChange(e.target.value === 'all' ? 'all' : Number(e.target.value))}
          className="bg-transparent focus:outline-none"
        >
          <option value="all">전체 학년</option>
          {gradeOptions.map((grade) => (
            <option key={grade} value={grade}>
              {grade}학년
            </option>
          ))}
        </select>
      </label>
    )}
    {showGoal && (
      <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 border border-slate-200 rounded-full font-semibold text-xs">
        <FilterIcon className="w-4 h-4 text-primary" />
        <div className="flex gap-1">
          {[
            { value: 'all', label: '전체' },
            { value: 'work', label: '취업 준비' },
            { value: 'university', label: '대학 준비' },
          ].map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => onGoalChange(opt.value as typeof goalFilter)}
              className={`px-2 py-1 rounded-full border ${
                goalFilter === opt.value
                  ? 'bg-primary text-white border-primary'
                  : 'bg-white text-slate-700 border-slate-200 hover:border-primary/60'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
    )}
    <label className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 border border-slate-200 rounded-full font-semibold text-xs">
      <SortIcon className="w-4 h-4 text-primary" />
      <select
        value={sortOption}
        onChange={(e) => onSortChange(e.target.value as typeof sortOption)}
        className="bg-transparent focus:outline-none"
      >
        <option value="recent">최신순</option>
        <option value="score">점수순</option>
        <option value="growth">개선율</option>
      </select>
    </label>
  </div>
);

export default FilterControls;
