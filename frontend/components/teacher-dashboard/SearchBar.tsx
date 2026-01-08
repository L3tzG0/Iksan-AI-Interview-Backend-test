import type { FC } from 'react';
import type { SearchBarProps } from '../../types/teacherDashboard';
import { SearchIcon } from '../icons';

const SearchBar: FC<SearchBarProps> = ({ value, onChange, placeholder }) => (
  <div className="flex flex-1 items-center gap-3 bg-white/90 shadow-inner shadow-white/60 px-4 py-2 border border-slate-200 rounded-full">
    <SearchIcon className="w-5 h-5 text-primary" />
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="flex-1 bg-transparent focus:outline-none text-sm"
    />
  </div>
);

export default SearchBar;
