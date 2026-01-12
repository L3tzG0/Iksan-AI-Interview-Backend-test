import React, { useMemo, useState, useEffect } from 'react';
import { Info } from 'lucide-react';
import Card from '../Card';
import Button from '../ui/Button';
import SearchBar from '../teacher-dashboard/SearchBar';
import Input from '../ui/Input';
import { useToast } from '../ui/Toast';
import { fetchDomains, createDomain, updateDomain, deleteDomain, type DomainRecord } from '../../services/domainService';
import Spinner from '../Spinner';

type ModalMode = 'add' | 'edit';

const AdminDomainManagement: React.FC = () => {
  const { addToast } = useToast();
  const [searchTerm, setSearchTerm] = useState('');
  const [domains, setDomains] = useState<DomainRecord[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<ModalMode>('add');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [formValues, setFormValues] = useState({ organizationName: '', domainEmail: '' });
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const protectedDomain = '@students.internal';

  const loadDomains = async () => {
    setIsLoading(true);
    try {
      const backendDomains = await fetchDomains(searchTerm || undefined);
      const records: DomainRecord[] = backendDomains.map(d => ({
        id: d.id,
        organizationName: d.description,
        domainEmail: `@${d.domain}`,
      }));
      setDomains(records);
    } catch (error) {
      console.error('Failed to fetch domains:', error);
      addToast('도메인 목록을 불러오는데 실패했습니다.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDomains();
  }, [searchTerm]);

  const openAddModal = () => {
    setModalMode('add');
    setEditingId(null);
    setFormValues({ organizationName: '', domainEmail: '' });
    setFormError(null);
    setIsModalOpen(true);
  };

  const openEditModal = (domain: DomainRecord) => {
    setModalMode('edit');
    setEditingId(domain.id);
    setFormValues({ organizationName: domain.organizationName, domainEmail: domain.domainEmail });
    setFormError(null);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setFormError(null);
  };

  const handleSave = async (event: React.FormEvent) => {
    event.preventDefault();
    const organizationName = formValues.organizationName.trim();
    const domainEmail = formValues.domainEmail.trim();

    if (!organizationName || !domainEmail) {
      setFormError('조직명과 도메인 이메일을 모두 입력해주세요.');
      return;
    }

    if (!domainEmail.startsWith('@')) {
      setFormError('도메인 이메일은 @로 시작해야 합니다.');
      return;
    }

    const domain = domainEmail.slice(1); // remove @

    try {
      if (modalMode === 'add') {
        await createDomain({ domain, description: organizationName });
        addToast('도메인이 추가되었습니다.', 'success');
      } else if (editingId) {
        await updateDomain(editingId, { domain, description: organizationName });
        addToast('도메인이 수정되었습니다.', 'success');
      }
      loadDomains();
      closeModal();
    } catch (error) {
      console.error('Failed to save domain:', error);
      setFormError('저장 실패했습니다.');
    }
  };

  const openDeleteModal = (domainId: number) => {
    const target = domains.find((domain) => domain.id === domainId);
    if (target && target.domainEmail.toLowerCase() === protectedDomain) {
      addToast('해당 도메인은 삭제할 수 없습니다.', 'error');
      return;
    }
    setDeletingId(domainId);
    setIsDeleteOpen(true);
  };

  const closeDeleteModal = () => {
    setDeletingId(null);
    setIsDeleteOpen(false);
  };

  const confirmDelete = async () => {
    if (!deletingId) return;
    const target = domains.find((domain) => domain.id === deletingId);
    if (target && target.domainEmail.toLowerCase() === protectedDomain) {
      addToast('해당 도메인은 삭제할 수 없습니다.', 'error');
      closeDeleteModal();
      return;
    }
    try {
      await deleteDomain(deletingId);
      addToast('도메인이 삭제되었습니다.', 'success');
      loadDomains();
      closeDeleteModal();
    } catch (error) {
      console.error('Failed to delete domain:', error);
      addToast('도메인 삭제에 실패했습니다.', 'error');
    }
  };

  const deletingDomain = domains.find((item) => item.id === deletingId);
  const isEmpty = domains.length === 0;
  const isTableEmpty = !isLoading && isEmpty;

  return (
    <div className="space-y-8 mx-auto animate-fadeIn">
      <div className="space-y-2">
        <h1 className="font-bold text-slate-900 text-2xl">도메인 관리</h1>
        <p className="text-slate-600 text-sm">업무용 이메일 도메인만 허용됩니다. 예: @company.com</p>
      </div>

      <Card className="space-y-6">
        <div className="flex sm:flex-row flex-col sm:justify-between sm:items-center gap-3">
          <div className="w-full sm:max-w-md">
            <SearchBar
              value={searchTerm}
              onChange={setSearchTerm}
              placeholder="조직명 또는 도메인으로 검색"
            />
          </div>
          <Button type="button" onClick={openAddModal}>
            도메인 추가
          </Button>
        </div>

        {isTableEmpty ? (
          <div className="space-y-2 bg-slate-50 p-10 border border-slate-200 border-dashed rounded-2xl text-center">
            <p className="font-semibold text-slate-700">등록된 도메인이 없습니다.</p>
            <p className="text-slate-500 text-sm">도메인을 추가하면 업무용 이메일만 허용됩니다.</p>
            <Button type="button" variant="secondary" onClick={openAddModal} className="mt-2">
              도메인 추가
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-slate-700 text-sm text-left">
              <thead>
                <tr className="border-slate-100 border-b text-slate-400 text-xs uppercase tracking-wide">
                  <th scope="col" className="px-4 py-3">조직명</th>
                  <th scope="col" className="px-4 py-3">도메인 이메일</th>
                  <th scope="col" className="px-4 py-3 text-right">작업</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {isLoading && domains.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-4 py-6 text-slate-400 text-center">
                      <Spinner />
                    </td>
                  </tr>
                )}
                {domains.map((domain) => {
                  const isProtected = domain.domainEmail.toLowerCase() === protectedDomain;
                  return (
                    <tr key={domain.id} className="hover:bg-slate-50/70">
                      <td className="px-4 py-3 font-semibold text-slate-800">{domain.organizationName}</td>
                      <td className="px-4 py-3 text-black">{domain.domainEmail}</td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end items-center gap-2">
                          {isProtected ? (
                            <button
                              type="button"
                              onClick={() => addToast('해당 도메인은 수정/삭제할 수 없습니다.', 'info')}
                              className="text-slate-400 hover:text-slate-600"
                              aria-label="도메인 보호됨"
                            >
                              <Info className="w-4 h-4" />
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => openEditModal(domain)}
                              className="font-semibold text-primary hover:text-primary-dark text-sm"
                            >
                              수정
                            </button>
                          )}
                          {!isProtected && (
                            <button
                              type="button"
                              onClick={() => openDeleteModal(domain.id)}
                              className="font-semibold text-rose-500 hover:text-rose-600 text-sm"
                            >
                              삭제
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {isModalOpen && (
        <div className="z-50 fixed inset-0 flex justify-center items-center bg-slate-900/40 backdrop-blur-sm px-4">
          <div className="space-y-4 bg-white shadow-2xl p-6 border border-white/70 rounded-2xl w-full max-w-lg animate-softFadeUp">
            <div className="flex justify-between items-start gap-3">
              <div>
                <p className="font-semibold text-primary text-xs uppercase tracking-[0.2em]">관리자</p>
                <h3 className="mt-1 font-bold text-slate-900 text-xl">
                  {modalMode === 'add' ? '도메인 추가' : '도메인 수정'}
                </h3>
              </div>
              <button
                type="button"
                onClick={closeModal}
                className="font-bold text-slate-400 hover:text-slate-700 text-lg"
                aria-label="닫기"
              >
                x
              </button>
            </div>

            <form className="space-y-3" onSubmit={handleSave}>
              <Input
                label="조직명"
                value={formValues.organizationName}
                onChange={(event) => setFormValues((prev) => ({ ...prev, organizationName: event.target.value }))}
                placeholder="예: Iksan University"
                required
              />
              <Input
                label="도메인 이메일"
                value={formValues.domainEmail}
                onChange={(event) => setFormValues((prev) => ({ ...prev, domainEmail: event.target.value }))}
                placeholder="예: @company.com"
                required
              />
              <p className="text-slate-500 text-xs">도메인은 @로 시작해야 합니다.</p>
              {formError && <p className="font-semibold text-rose-600 text-sm">{formError}</p>}
              <div className="flex flex-wrap justify-end gap-2">
                <Button type="button" variant="secondary" onClick={closeModal}>
                  취소
                </Button>
                <Button type="submit">
                  {modalMode === 'add' ? '저장' : '변경사항 저장'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {isDeleteOpen && (
        <div className="z-50 fixed inset-0 flex justify-center items-center bg-slate-900/40 backdrop-blur-sm px-4">
          <div className="space-y-4 bg-white shadow-2xl p-6 border border-white/70 rounded-2xl w-full max-w-md animate-softFadeUp">
            <div className="flex justify-between items-center gap-3">
              <h3 className="font-bold text-slate-900 text-lg">도메인 삭제</h3>
              <button
                type="button"
                onClick={closeDeleteModal}
                className="font-bold text-slate-400 hover:text-slate-700 text-lg"
                aria-label="닫기"
              >
                x
              </button>
            </div>
            <p className="text-slate-600 text-sm">
              정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
            </p>
            {deletingDomain && (
              <div className="bg-slate-50 px-4 py-3 border border-slate-100 rounded-xl text-slate-700 text-sm">
                대상: <span className="font-semibold">{deletingDomain.domainEmail}</span>
              </div>
            )}
            <div className="flex flex-wrap justify-end gap-2">
              <Button type="button" variant="secondary" onClick={closeDeleteModal}>
                취소
              </Button>
              <Button type="button" variant="danger" onClick={confirmDelete}>
                삭제
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDomainManagement;

