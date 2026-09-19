import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { HumanReview } from './HumanReview'

describe('HumanReview', () => {
  it('no sustituye una decisión RECHAZAR guardada por APROBAR', async () => {
    const save = vi.fn(async () => {})
    render(<HumanReview kind="case1" resourceId="a1" reviewStatus="REVISADA" initialDecision="RECHAZAR" onSubmit={save} />)
    expect(screen.getByLabelText('Decisión humana')).toHaveValue('RECHAZAR')
    fireEvent.click(screen.getByRole('button', { name: 'Guardar revisión' }))
    await waitFor(() => expect(save).toHaveBeenCalledWith('RECHAZAR', 'Revision humana completada.', null))
  })
})
